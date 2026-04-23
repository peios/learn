---
title: Phase 2
---

With registryd running, peinit reads the service graph from the
registry and boots the system. Phase 2 is entirely registry-driven.

## Step 1: Read service definitions and mount configuration

peinit MUST read all entries under `Machine\System\Services\` from
the registry. Each key contains a service definition (see the
Service Model section). These reads are bounded by LCS's request
timeout -- if registryd hangs mid-read, peinit receives ETIMEDOUT
and MUST enter Recovery mode.

Only services with a `boot` trigger are candidates for automatic
start. Services with no triggers (demand-only) wait for explicit
start commands. Services with `Disabled=1` MUST NOT be included in the boot
graph. Their definitions are still loaded into peinit's in-memory
model for on-demand start via the control interface.

peinit MUST also read mount entries from
`Machine\System\Boot\Mounts\`. Each mount entry generates a
pseudo-service named `mount:<mountpoint>` (e.g., `mount:/data`).

Mount pseudo-services behave as Oneshot services with
RemainAfterExit. The mount operation completes, the pseudo-service
stays in the Completed state, and dependents can start. Services
that need a mount point declare it as a dependency:
`Requires = ["mount:/data"]`.

Mount pseudo-services MUST run `fsck` on the target device before
mounting if the mount configuration specifies it. Root filesystem
fsck is handled by the initramfs (see the Bootstrap section), not
peinit.

## Step 2: Build and validate the dependency graph

peinit MUST perform a topological sort of all boot-triggered
services -- including mount pseudo-services -- and validate the
graph before attempting to start anything. The full validation
rules are defined in the Dependencies section. The key outcomes:

- **Cycle detected:** all services in the cycle are marked Failed.
  If the cycle involves a Critical service, peinit MUST downgrade
  to Safe mode without rebooting.
- **Unresolvable conflict:** both services are marked Failed. Same
  Safe mode escalation if either is Critical.
- **Missing Requires dependency:** the dependent is marked Failed.
- **Validation warnings** (e.g., Readiness=Alive with dependents)
  are logged but do not prevent boot.

Mount pseudo-services participate in the dependency graph. During
shutdown, unmount happens after all services that Require the mount
have stopped.

## Step 3: Start services in dependency order

peinit MUST walk the dependency graph and start services,
parallelising where the graph allows. Services are started up to
a configurable concurrency limit:

| Registry key | Default | Description |
|---|---|---|
| `Machine\System\Boot\MaxParallelStarts` | 10 | Maximum services starting concurrently. |

As each service reaches a satisfied state (Active for Simple,
Completed for Oneshot -- both with and without RemainAfterExit),
its dependents become eligible and are added to the start queue.
A Oneshot without RemainAfterExit transitions Starting -> Completed
(releasing dependents) -> Inactive.

The typical Phase 2 boot order, determined by the dependency graph:

1. **eudev** -- device management. Runs as SYSTEM with
   RequiredPrivileges stripped to the minimum eudev needs. Starts
   before authd is available.
2. **lpsd** -- local identity database. Depends on registryd only.
   Runs as SYSTEM.
3. **authd** -- identity authority. Depends on registryd and lpsd.
   Runs as SYSTEM. Once authd signals readiness, the token minting
   flow is available.
4. **eventd** -- logging and audit. Runs as SYSTEM. Services
   started before eventd log to peinit's pre-eventd buffer.
5. **Networking** -- network interface configuration. First service
   to receive a token via authd.
6. **Application services** -- in dependency order, parallelised
   where possible.
7. **Login services** -- started last so the system is fully
   operational before accepting user sessions.

> [!INFORMATIVE]
> This ordering is not hardcoded -- it emerges from the dependency
> graph. The list above describes the typical result of standard
> role definitions. An administrator who changes dependencies will
> get a different order.

## Readiness gating

A service's dependents MUST NOT start until the service satisfies
its dependents. The satisfaction rules are:

- **Simple service:** satisfies dependents when it signals
  `READY=1` (Readiness=Notify) or when the process is alive
  (Readiness=Alive).
- **Oneshot service:** satisfies dependents when the process exits
  successfully and the service reaches the Completed state.
- **Skipped service:** satisfies dependents immediately (the
  service does not apply to this system).

If a service fails to reach readiness within its StartTimeout:

- **Requires dependents:** MUST transition to Failed with cause
  DependencyFailure.
- **Wants dependents:** MUST start regardless.

## Bootstrap matrix

| Service | Phase | Identity | Token source | Readiness | ErrorControl |
|---|---|---|---|---|---|
| registryd | 1 | SYSTEM | SYSTEM clone | sd_notify | Critical |
| eudev | 2 | SYSTEM | SYSTEM clone (privileges stripped) | process alive | Normal |
| lpsd | 2 | SYSTEM | SYSTEM clone | sd_notify | Critical |
| authd | 2 | SYSTEM | SYSTEM clone | sd_notify | Critical |
| eventd | 2 | SYSTEM | SYSTEM clone | sd_notify | Critical |
| networking | 2 | service token | authd | sd_notify | Normal |
| sshd | 2 | service token | authd | process alive | Normal |
| app services | 2 | service token | authd | per-service | Normal |

## Phase 2 failure summary

| Failure | Response |
|---|---|
| Service definition fails validation | Service marked Failed (ValidationError). Other services continue. |
| Dependency cycle detected | All services in cycle marked Failed. If cycle involves Critical service: Safe mode. |
| Missing Requires dependency | Dependent marked Failed. |
| Critical service fails during boot | Restart budget -> reboot. |
| Non-critical service fails during boot | Service marked Failed. Requires dependents also fail. Other services continue. |
| authd unavailable when service needs a token | Service marked Failed. |
| Mount pseudo-service fails | Service marked Failed. Requires dependents also fail. |
| Registry read times out during Step 1 | Recovery mode. |

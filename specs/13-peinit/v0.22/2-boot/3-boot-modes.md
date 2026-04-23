---
title: Boot Modes
---

peinit has three boot modes, forming an escalation path from normal
operation to last-resort maintenance.

## Full mode

Full mode is the default. All boot-triggered services start in
dependency order as described in the Phase 2 section.

A successful Full boot MUST reset the boot attempt counter to 0.
A boot is successful when all Critical services have been Active
for a grace period:

| Registry key | Default | Description |
|---|---|---|
| `Machine\System\Boot\BootSuccessGrace` | 30 | Seconds all Critical services must remain Active before the boot is considered successful. |

## Safe mode

Safe mode starts a reduced set of services. Two categories of
services are eligible:

- **Critical services** (`ErrorControl=Critical`): MUST start. If
  a Critical service fails in Safe mode, the normal Critical
  failure path applies (restart budget, reboot, counter increment,
  eventual Recovery).
- **SafeMode services** (`SafeMode=1`): best-effort. peinit
  attempts to start them, but if they fail, Safe mode continues
  without them.

All other services are skipped.

peinit MUST rebuild the dependency graph from scratch using only
eligible services (Critical + SafeMode=1). Dependencies on
excluded services are dropped -- if service A depends on non-
Critical service B, and B is excluded, A's dependency on B does
not exist in the Safe mode graph.

A successful Safe boot MUST reset the boot attempt counter to 0.

> [!INFORMATIVE]
> Safe mode is purely a boot sequencing concern -- it controls
> which services auto-start. Once booted, the administrator can
> start any service manually, exactly as in Full mode. Safe mode is
> for situations where the system configuration is broken but the
> TCB itself is healthy.

`SafeMode=1` is a filter within the boot-triggered set. A service
with no `boot` trigger does not auto-start in Safe mode regardless
of its SafeMode flag.

### Entry conditions

- **Cycle involving a Critical service at boot:** if dependency
  graph validation detects a cycle that includes a Critical
  service, peinit MUST downgrade to Safe mode without rebooting.
  The cycle is a configuration error -- rebooting would hit the
  same cycle.
- **Unresolvable conflict involving a Critical service at boot:**
  if two boot-triggered services conflict and either has
  ErrorControl=Critical, peinit MUST downgrade to Safe mode
  without rebooting. Same reasoning as cycles -- the conflict is
  a configuration error.
- **Kernel command line:** `peios.safemode=1` forces Safe mode.

Safe mode is NOT entered due to a Critical service crash at
runtime. That follows the normal path: restart budget, reboot,
counter increment, Recovery.

## Recovery mode

Recovery mode is peinit's last resort. There is no TCB guarantee.
The administrator gets an unrestricted SYSTEM shell on the console.

### Entry conditions

- **Boot attempt counter >= N** (configurable, default 3). peinit
  reads the counter from `/.peinit/boot-attempts` on startup. The
  counter increments on each boot. Critical service failures (at
  any time, boot or runtime) trigger sync and reboot, which
  increments the counter on next boot.
- **Kernel command line:** `peios.recovery=1` forces Recovery
  regardless of counter.
- **Phase 1 registryd failure:** if registryd fails during Phase 1,
  peinit MUST enter Recovery immediately -- no reboot, no counter
  increment. Without a working registry there is no Phase 2 to
  boot into.

### Behaviour

When entering Recovery mode, peinit MUST:

1. Complete Phase 1 steps 1-3 (remount root read-write, mount
   virtual filesystems, set clock from RTC) if not already done.
2. Attempt to start registryd. If registryd fails, ignore the
   failure and continue. Recovery mode MUST deliver a shell
   regardless of registryd's state.
3. Skip all Phase 2 services.
4. Start a root shell on the console using a compiled-in definition
   (no registry dependency).
5. Log the failure reason to console.

> [!INFORMATIVE]
> Recovery mode is NOT a degraded boot -- it is a maintenance
> environment. There are no underlying security protections beyond
> what the kernel provides. The administrator has a SYSTEM shell
> and must treat it with corresponding care.

### Offline registry access

If registryd itself caused the recovery, the administrator needs
tools that work without registryd. Three recovery paths MUST be
available:

1. **Inspection:** `loregd --inspector` reads the storage database
   directly, bypassing LCS, for diagnosis.
2. **Backup restore:** `loregd --recover-from-backup` restores
   from an automatic backup taken on every registryd startup.
3. **Database clear:** `loregd --dangerously-clear-database` wipes
   the registry entirely. Role definitions are the source of truth
   for service configuration, so a cleared registry is
   recoverable.

> [!INFORMATIVE]
> The recovery tools reference loregd directly because in recovery
> mode the administrator is interacting with the storage
> implementation, not with the registry abstraction. This is the
> one context where the distinction between registryd (the service
> peinit manages) and loregd (the implementation) is visible to the
> administrator.

### Remote recovery

Recovery mode requires console access (physical, IPMI, or serial).
Post-v1 features to address headless servers:

- **Registry historical reversion:** roll back to a last-known-good
  registry state from the recovery shell.
- **Emergency SSH:** a static sshd started without registry
  involvement, enabling remote access to the recovery environment.

## Boot attempt counter

peinit MUST maintain a boot attempt counter at
`/.peinit/boot-attempts`. The counter is a plain integer stored in
a file on the root filesystem (not in the registry, because the
registry may be the reason for the failure).

- The counter MUST be incremented at the start of every boot,
  before Phase 1 begins.
- The counter MUST be reset to 0 on a successful Full or Safe boot
  (after the grace period).
- If the counter file cannot be written (e.g., disk full), peinit
  MUST treat the counter as 0 and continue. A write failure MUST
  NOT trigger Recovery mode.

## Escalation summary

```
Full boot ---+-- success ----------------> counter reset, operational
             |
             +-- cycle w/ Critical ------> Safe mode (no reboot)
             |
             +-- conflict w/ Critical ---> Safe mode (no reboot)
             |
             +-- Critical failure -------> sync + reboot --+
                                                            |
Safe boot ---+-- success ----------------> counter reset,   |
             |   operational (reduced)                      |
             +-- Critical failure -------> sync + reboot ---+
                                                            |
                              counter increments <----------+
                                         |
                              counter >= N ---------> Recovery mode
                              Phase 1 failure ------> Recovery mode
```

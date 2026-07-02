---
title: peinit at PID 1
type: concept
description: peinit is the init system of the real root, signed at TCB trust level, running with the SYSTEM token — it takes over once the initramfs has mounted the real root. It is responsible for the rest of userspace boot — bringing up the platform, launching services in dependency order, transitioning to a steady-state system. This page covers what peinit does, why it has to be PID 1, and the service-launching pattern that's its primary job.
related:
  - peios/peinit/overview
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/authd-handoff
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/pip-in-practice
---

**peinit** is the init system of a running Peios system — the process that takes over once the [initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage) has mounted the real root. It runs at PID 1, signed at TCB level, holding the SYSTEM token. From there, peinit does the rest of the work needed to bring the system from a freshly-mounted real root to "fully-running with services and users".

The specific responsibilities are:

- Run the compiled-in Phase 1 bootstrap: probe that the root is writable, mount the virtual filesystems, restore the random seed, ensure the machine-id, set the clock from the RTC, and start registryd.
- Read the service catalog from the registry (`Machine\System\Services\`), validate the dependency graph, and start services in dependency order — authd among them.
- Mint SYSTEM tokens for platform services itself; request every other identity from authd.
- Continue running as the system's lifecycle manager — handling service crashes, system shutdown, eventual reboot.

This page covers each of these responsibilities, why peinit specifically is the right thing to be PID 1, and the patterns peinit uses for the work.

> [!NOTE]
> This page is about peinit's place in the **boot and trust chain** — why it is PID 1, the identity it holds, and how it hands off to the rest of userspace. The full **service-manager model** — the service definition schema, the state machine, dependencies, supervision and restart policy, timers, jobs and operations, and the control interface — has its own topic. Start at [peinit](~peios/peinit/overview).

## Why peinit at PID 1

PID 1 has special properties in Linux: it cannot be killed by ordinary signals, it inherits orphaned processes, it's the ancestor of everything else. Whichever process is PID 1 is operationally critical.

Peios chooses peinit specifically because:

- **It's signed at TCB level.** When peinit is exec'd — by prelude, at the switch to the real root — the signature verification at exec sets `pip_type = Protected`, `pip_trust = 8192`. peinit is now PIP-protected at the highest level. No other process can signal it, debug it, or interfere with it.
- **It runs on the SYSTEM token.** Inherited from init. peinit has every privilege; it can do anything that requires authority.
- **It's purpose-built for the bootstrap.** Other init-style processes do general-purpose process management; peinit specifically knows about Peios's identity model, its registry-defined service catalog, and the service-launching pattern Peios uses.

The combination of "PIP-protected" and "all privileges" and "purpose-built" makes peinit the right thing to be PID 1. A general-purpose init that wasn't signed at TCB level would be a weak link — every TCB-level process (authd, loregd, eventd) is unreachable by their lifecycle manager, which means lifecycle management could only be done by another TCB-level process. That role is peinit.

## The TCB lifecycle-manager pattern

A consequence of PIP: only a process that PIP-dominates the TCB daemons can signal them. Since the TCB daemons are at `pip_type = Protected, pip_trust = 8192`, only another process at the same level (or higher, but there is no higher in v0.20) can dominate.

peinit is the only such process at the right time. peinit is signed at TCB level, so it dominates. authd, loregd, eventd, lpsd are also at TCB level, so they dominate each other — but they don't manage each other's lifecycles by convention. peinit is the conventional lifecycle manager.

This is documented in [PIP in practice](~peios/process-integrity-protection/pip-in-practice). The TCB-lifecycle-management pattern is a consequence of PIP; peinit happens to be the binary that fills the role.

## What peinit does at startup

peinit's startup is two phases. The authoritative, step-by-step account lives in the peinit topic at [Boot and boot modes](~peios/peinit/boot-and-boot-modes); what follows is the trust-chain summary.

### Phase 1 — compiled-in bootstrap

Phase 1 runs before any configuration is available, in a fixed order compiled into the binary:

1. **Assert PID 1.** peinit refuses to run as anything else.
2. **Probe that the real root is writable**, and ensure the virtual filesystems (`/proc`, `/sys`, `/dev`, …) are mounted.
3. **Restore the random seed, ensure the machine-id, set the clock from the RTC.**
4. **Start registryd** and probe the registry schema. The registry is the source of all subsequent configuration, so its daemon comes up before anything else.
5. **Provision boot paths and infrastructure** — the control socket, the job filesystem, loopback networking.

### Phase 2 — the service graph

With the registry available, peinit reads the service catalog from `Machine\System\Services\`, validates the dependency graph, and starts services in dependency order. authd is an ordinary Critical service in this graph — started after the infrastructure it depends on (eudev, lpsd), gated by the same readiness mechanics as any other service, not by a special wait-for-authd phase.

For each service, the pattern is **fork-install-exec**:

1. peinit obtains the service's token — minted by peinit itself for SYSTEM/platform services, requested from authd for every other identity (see [Identity and privileges](~peios/peinit/identity-and-privileges)).
2. peinit forks; the child inherits a SYSTEM-derived token.
3. peinit installs the service-specific token on the child via `KACS_IOC_INSTALL`.
4. The child execs the service binary. The kernel verifies the signature and sets the PIP fields.

> [!NOTE]
> PSD-004 (KACS) assigns two further boot jobs to peinit — populating the machine-wide TLP cache from the registry, and applying per-service mitigation flags via `kacs_set_psb` between fork and exec — but neither is part of peinit's specified or implemented behaviour yet (PSD-007 v0.22 defines no such steps). Mount-policy application (`kacs_set_mount_policy`) and boot-time CAAP distribution are likewise not peinit responsibilities today; CAAP distribution belongs to authd and is currently deferred.

### Steady state

After the graph is started, peinit transitions to its steady-state role: the lifecycle manager. It watches for service crashes (a child process dies; peinit receives SIGCHLD), restarts them per policy, handles shutdown signals (an administrator calling `shutdown`), and otherwise runs as a long-lived daemon.

The system is now "up" — services are running, authd is creating tokens for users who sign in, FACS and KACS are enforcing access control, audit events are flowing through KMES.

## The fork-install-exec pattern

The pattern is the most important thing peinit does, and it's worth pinning. The order of operations is deliberate:

1. **fork.** Creates the child process. The child inherits the parent's token, file descriptors, and PSB. At this point the child is essentially a clone of peinit.
2. **Install token.** The child gets its service-specific token via `KACS_IOC_INSTALL`. This is the moment its identity is set to be the right thing for the service.
3. **exec.** The new program runs. The kernel verifies the binary's signature and sets the PIP fields.

The reason for this order: the service's token needs to be in place before the service's startup code runs — the service should be able to assume from its first instruction that it's running as the right identity. exec comes last because that is the moment the new program takes over; by then the identity has been decided.

The pattern is what every service is launched through. Variations are minor — the specific token differs per service — but the structural sequence is the same. (When per-service mitigations land in peinit — see the note above — they will slot in between install and exec, since mitigation flags must be on the PSB before the new binary runs.)

## What peinit does *not* do

A few clarifications:

- **peinit mints only SYSTEM tokens.** Minting the SYSTEM token for platform services via `kacs_create_token` is peinit's normal, specified path — no authd interaction is needed for those. Every other identity is requested from authd, the source of truth for who-gets-what privileges.
- **peinit is not the only TCB process.** authd, loregd, eventd, lpsd are also at TCB level. They have their own jobs.
- **peinit does not enforce policy.** DACLs, conditional ACEs, mount policies — the kernel runs AccessCheck and makes every access decision; peinit just launches processes with the right identities.
- **peinit does not handle user sessions directly.** Users sign in via authd; authd produces tokens; peinit launches the session's first process. The user's session is managed by authd, not peinit.
- **peinit's service management is peinit, not a separate daemon.** Start order, dependencies, restart policy, the service state machine, and the control interface are peinit's own responsibility — there is no service-manager process living alongside it. That model is substantial enough to have its own topic; this page does not cover it. See [peinit](~peios/peinit/overview).

## When peinit fails

If peinit crashes or exits, the kernel typically panics — losing PID 1 is a system-fatal condition in Linux. Peios's peinit is built to be very stable for this reason; its work is narrow and bounded.

If peinit cannot complete a startup step (a service won't launch, authd won't start, mount policy can't be applied), the deployment-specific behaviour depends on the configured policy. Typical responses:

- For a critical failure (authd won't start), boot fails. The system enters a recovery state — typically a console login as SYSTEM, with limited services running, enough for an administrator to diagnose and fix.
- For a non-critical failure (a single service won't start), peinit logs the failure, leaves the service unstarted, and continues with the rest of boot.

The failure-mode behaviour is configurable but conservative by default. peinit doesn't try to "work around" failures by relaxing security; if the configured set of mitigations can't be applied, the service doesn't start rather than starting unhardened.

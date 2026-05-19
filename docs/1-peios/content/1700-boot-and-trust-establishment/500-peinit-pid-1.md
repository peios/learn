---
title: peinit at PID 1
type: concept
description: peinit is the init system of the real root, signed at TCB trust level, running with the SYSTEM token — it takes over once the initramfs has mounted the real root. It is responsible for the rest of userspace boot — applying mount policies, launching services, transitioning to a steady-state system. This page covers what peinit does, why it has to be PID 1, and the service-launching pattern that's its primary job.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/authd-handoff
  - peios/process-integrity-protection/overview
  - peios/process-integrity-protection/pip-in-practice
---

**peinit** is the init system of a running Peios system — the process that takes over once the [initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage) has mounted the real root. It runs at PID 1, signed at TCB level, holding the SYSTEM token. From there, peinit does the rest of the work needed to bring the system from a freshly-mounted real root to "fully-running with services and users".

The specific responsibilities are:

- Apply mount policies to filesystems.
- Push any boot-time CAAP via `kacs_set_caap`.
- Populate the TLP (Trusted Library Paths) cache from configuration.
- Launch authd.
- Wait for authd to be ready.
- Launch the remaining services, each with the appropriate token (from authd) and the appropriate mitigation flags applied.
- Continue running as the system's lifecycle manager — handling service crashes, system shutdown, eventual reboot.

This page covers each of these responsibilities, why peinit specifically is the right thing to be PID 1, and the patterns peinit uses for the work.

## Why peinit at PID 1

PID 1 has special properties in Linux: it cannot be killed by ordinary signals, it inherits orphaned processes, it's the ancestor of everything else. Whichever process is PID 1 is operationally critical.

Peios chooses peinit specifically because:

- **It's signed at TCB level.** When peinit is exec'd — by prelude, at the switch to the real root — the signature verification at exec sets `pip_type = Protected`, `pip_trust = 8192`. peinit is now PIP-protected at the highest level. No other process can signal it, debug it, or interfere with it.
- **It runs on the SYSTEM token.** Inherited from init. peinit has every privilege; it can do anything that requires authority.
- **It's purpose-built for the bootstrap.** Other init-style processes do general-purpose process management; peinit specifically knows about Peios's identity model, mount policies, CAAP distribution, and the service-launching pattern Peios uses.

The combination of "PIP-protected" and "all privileges" and "purpose-built" makes peinit the right thing to be PID 1. A general-purpose init that wasn't signed at TCB level would be a weak link — every TCB-level process (authd, loregd, eventd) is unreachable by their lifecycle manager, which means lifecycle management could only be done by another TCB-level process. That role is peinit.

## The TCB lifecycle-manager pattern

A consequence of PIP: only a process that PIP-dominates the TCB daemons can signal them. Since the TCB daemons are at `pip_type = Protected, pip_trust = 8192`, only another process at the same level (or higher, but there is no higher in v0.20) can dominate.

peinit is the only such process at the right time. peinit is signed at TCB level, so it dominates. authd, loregd, eventd, lpsd are also at TCB level, so they dominate each other — but they don't manage each other's lifecycles by convention. peinit is the conventional lifecycle manager.

This is documented in [PIP in practice](~peios/process-integrity-protection/pip-in-practice). The TCB-lifecycle-management pattern is a consequence of PIP; peinit happens to be the binary that fills the role.

## What peinit does at startup

The full peinit startup sequence, in order:

### 1. Verify own integrity

Before doing anything operationally meaningful, peinit verifies it is running in the right state — PID 1, PIP-protected at TCB level, holding the SYSTEM token. Anything else indicates the boot is broken; peinit refuses to proceed.

This is defensive coding: peinit could be exec'd by an attacker who somehow inserted themselves between the initramfs and peinit. The verification catches that case. In normal operation it always passes.

### 2. Apply mount policies

peinit reads the mount-policy configuration from the registry (or compiled-in defaults if the registry isn't available yet) and applies each policy via `kacs_set_mount_policy`. This is what establishes the FACS behaviour for each filesystem — what's `facs_deny_missing`, what's `facs_synthesize_ephemeral`, etc.

Mount policies need to be applied before any services start using their filesystems. Without a policy applied, FACS may default to a different behaviour than the deployment expects; getting the policies in place first means every subsequent access uses the intended rules.

### 3. Populate the TLP cache

The Trusted Library Paths cache is a machine-wide kernel cache of approved directory prefixes that mitigation-enabled processes can load libraries from. peinit reads the TLP configuration (from the registry) and populates the cache.

The cache is populated **before** any services are launched — services that have TLP enabled need the cache to be in place when they try to `mmap(PROT_EXEC)` libraries. A service starting with an empty TLP cache would have every library load refused.

### 4. Push early-boot CAAP

Some deployments have central access policies that need to be active before services start. peinit pushes these (via `kacs_set_caap`) so that the recovery policy isn't applied for objects covered by such CAAP during the rest of boot.

This is a peinit-only operation in normal operation; authd will subsequently push the rest of the CAAP catalog. peinit handles only what needs to be in place very early.

### 5. Launch authd

peinit forks; the child becomes authd. The specific sequence:

1. peinit calls `fork()`.
2. The child runs early-startup code (still on the SYSTEM token).
3. The child calls `KACS_IOC_INSTALL` to install a specific authd-tailored token (or, more commonly, peinit uses `FilterToken` first to produce a narrower token, then `KACS_IOC_INSTALL`s that). The token typically has fewer privileges than the full SYSTEM token — authd doesn't need `SeLoadDriverPrivilege` or `SeShutdownPrivilege`.
4. peinit applies mitigations on the child via `kacs_set_psb` — WXP, LSV, TLP, CFIF, CFIB, PIE, etc. as appropriate.
5. The child calls `execve` on the authd binary. The kernel verifies the binary's signature (signed at TCB) and sets `pip_type = Protected, pip_trust = 8192` on the new process.
6. authd starts running.

peinit waits for authd to signal readiness — typically by authd writing a status fd, by reaching a steady state observable from peinit, or by authd's own startup protocol indicating completion.

### 6. Wait for authd to be ready

peinit blocks until authd has finished its own startup work — connecting to the directory, populating the CAAP cache, marking itself ready. While waiting, peinit may run other services that don't depend on authd (the registry daemon, observability daemons).

Services that depend on authd cannot start until this step completes. peinit's startup configuration declares the dependencies; peinit honours them.

### 7. Launch the rest of the services

Once authd is ready, peinit can launch the rest of userspace. For each service, the pattern is:

1. peinit asks authd for a token for this service. Authd consults the directory and produces a token with the appropriate identity, groups, privileges, claims for this service.
2. peinit forks. The child gets a SYSTEM-derived token initially (inherited).
3. peinit installs the service-specific token on the child via `KACS_IOC_INSTALL`.
4. peinit applies mitigations on the child PSB via `kacs_set_psb`.
5. The child execs the service binary. The kernel verifies signature, sets PIP fields.
6. The service starts running.

This is the "fork-install-mitigate-exec" pattern. Every service goes through it. The launching is centralised in peinit because peinit holds the necessary privileges and PIP authority.

### 8. Transition to steady state

After all services are launched, peinit transitions to its steady-state role: the lifecycle manager. It watches for service crashes (a child process dies; peinit receives SIGCHLD), restarts them per policy, handles shutdown signals (an administrator calling `shutdown`), and otherwise runs as a long-lived daemon.

The system is now "up" — services are running, authd is creating tokens for users who sign in, FACS and KACS are enforcing access control, audit events are flowing through KMES.

## The fork-install-mitigate-exec pattern

The pattern is the most important thing peinit does, and it's worth pinning. The order of operations is deliberate:

1. **fork.** Creates the child process. The child inherits the parent's token, file descriptors, and PSB. At this point the child is essentially a clone of peinit.
2. **Install token.** The child gets its service-specific token via `KACS_IOC_INSTALL`. This is the moment its identity is set to be the right thing for the service.
3. **Apply mitigations.** `kacs_set_psb` enables the mitigation flags the service needs. The flags are one-way; once on, they cannot be relaxed by the service itself.
4. **exec.** The new program runs. The kernel verifies the binary's signature and sets the PIP fields. The mitigations apply from this moment.

The reason for this order:

- Token install **before** exec: the service's token needs to be in place before the service's startup code runs. The service should be able to assume from its first instruction that it's running as the right identity.
- Mitigations **before** exec: same reasoning. The mitigations need to be in place before the new binary runs. PIE specifically requires the flag to be on the PSB before exec, because exec checks it.
- exec **after** install and mitigations: this is the moment the new program takes over. By this time, both the identity and the hardening posture have been decided. The new program inherits both.

The pattern is what every service is launched through. Variations are minor — the specific token and the specific mitigation set differ per service — but the structural sequence is the same.

## What peinit does *not* do

A few clarifications:

- **peinit does not create tokens directly.** It asks authd for tokens. The SYSTEM token has `SeCreateTokenPrivilege` (peinit could create tokens), but the convention is that authd is the source of truth for who-gets-what privileges. peinit can mint tokens directly in emergencies (when authd is not yet running) but normally delegates.
- **peinit is not the only TCB process.** authd, loregd, eventd, lpsd are also at TCB level. They have their own jobs.
- **peinit does not enforce policy.** Mount policies, DACLs, conditional ACEs — peinit applies them but doesn't make access decisions. The kernel runs AccessCheck; peinit just sets up the inputs.
- **peinit does not handle user sessions directly.** Users sign in via authd; authd produces tokens; peinit launches the session's first process. The user's session is managed by authd, not peinit.
- **peinit is not a service manager in the usual sense.** It launches services, but the "service management" concepts (start order, dependencies, restart policy) are part of peinit's configuration, not a separate service manager that lives alongside peinit.

## When peinit fails

If peinit crashes or exits, the kernel typically panics — losing PID 1 is a system-fatal condition in Linux. Peios's peinit is built to be very stable for this reason; its work is narrow and bounded.

If peinit cannot complete a startup step (a service won't launch, authd won't start, mount policy can't be applied), the deployment-specific behaviour depends on the configured policy. Typical responses:

- For a critical failure (authd won't start), boot fails. The system enters a recovery state — typically a console login as SYSTEM, with limited services running, enough for an administrator to diagnose and fix.
- For a non-critical failure (a single service won't start), peinit logs the failure, leaves the service unstarted, and continues with the rest of boot.

The failure-mode behaviour is configurable but conservative by default. peinit doesn't try to "work around" failures by relaxing security; if the configured set of mitigations can't be applied, the service doesn't start rather than starting unhardened.

---
title: Security Model
---

This section consolidates peinit's security architecture. Individual
mechanisms are defined in their respective sections; this section
defines the trust model, attack surfaces, and security invariants.

## Trust boundaries

peinit operates at two trust boundaries.

### Kernel to peinit

peinit is the first userspace process. The kernel assigns it a
SYSTEM token (`S-1-5-18`, all privileges). This is the root of
trust for all userspace identity. peinit MUST NOT drop this token
and MUST NOT authenticate to anyone -- its identity is axiomatic.

### peinit to services

peinit creates service processes with specific identities and
reduced privileges. The trust direction is one-way: peinit trusts
the kernel (it has no choice), and services trust peinit (it gave
them their identity). Services do not trust each other -- KACS
mediates all inter-service access.

peinit is part of the Trusted Computing Base (TCB), alongside the
kernel, KACS, LCS, KMES, registryd, authd, lpsd, and eventd. A
compromise of any TCB component compromises the entire system.

### Pre-FACS scope

The token, privilege, and SD enforcement described in this
specification is fully operational for IPC-mediated access
(registry, control socket, service-to-service communication).
However, pre-FACS, all processes run as UID 0 and the filesystem
does not enforce KACS Security Descriptors. A service's token
controls what it can access via KACS-protected interfaces but does
not prevent it from reading or writing arbitrary files on disk.

The peinit security model becomes fully effective for filesystem
objects once FACS is implemented. Until then, the filesystem layer
relies on conventional trust (correct packaging, controlled binary
paths).

## peinit's privileges

peinit runs as SYSTEM with all privileges for the lifetime of the
system. It requires:

- **PRIV_TCB** -- to request tokens from authd on behalf of
  services.
- **PRIV_IMPERSONATE** -- to impersonate control socket callers for
  AccessCheck evaluation.
- **Process creation** -- fork/exec authority (inherent to PID 1).
- **cgroup management** -- create/destroy cgroups under
  `/sys/fs/cgroup/peinit/`.
- **Signal delivery** -- SIGTERM/SIGKILL to managed processes.
- **Mount operations** -- Phase 1 virtual filesystem mounts.

peinit does not use PRIV_CREATE_TOKEN directly. Token creation is
authd's responsibility. peinit receives token fds from authd.

## Attack surface

| Surface | Who can reach it | What it controls | Protection |
|---|---|---|---|
| Control socket | Any process on the system. | Service lifecycle, shutdown. | KACS peer token + AccessCheck against ServiceSecurity SD. |
| Notify socket | Processes with NOTIFY_SOCKET env var. | Service readiness state. | PID matching via pidfd + start generation. |
| Registry keys | Any process with registry access. | Service definitions, triggers, config. | Registry key SDs (kernel-enforced via LCS). |
| Service cgroups | peinit only (creator). | Process tracking, clean kill. | cgroup hierarchy ownership. |
| Phase 1 mounts | peinit only. | VFS availability. | Hardcoded, no external input. |
| Boot attempt counter | peinit only (pre-FACS: any UID 0 process). | Recovery mode entry. | File on root filesystem. Pre-FACS, any process can tamper. |
| JFS device | Processes with PRIV_CREATE_JOB. | Ad-hoc job submission. | KACS privilege check (kernel-enforced by JFS). |

## Security invariants

Properties that peinit MUST NOT violate under any circumstances:

1. **peinit MUST NOT grant privileges it was not asked to grant.**
   RequiredPrivileges is subtractive only. peinit removes
   privileges; it MUST NOT add them.

2. **peinit MUST NOT bypass AccessCheck for control operations.**
   Every control socket command is checked against the appropriate
   SD. There is no backdoor, no override flag, no "trust
   localhost."

3. **peinit MUST NOT expose one service's state to another without
   access control.** The `list` command returns only services the
   caller has SERVICE_QUERY_STATUS on. Status queries are
   per-service access-controlled.

4. **peinit MUST log all access denials.** Failed AccessCheck
   results are logged with caller SID, target, and requested
   right. Silent denial is not acceptable.

5. **The control socket SD and ServiceSecurity SDs are the only
   policy inputs for runtime access control.** peinit MUST NOT
   consult any other source (config files, environment variables,
   hardcoded lists) for access decisions.

6. **peinit MUST NOT share its SYSTEM token.** Even
   `Identity=SYSTEM` services receive a clone, never peinit's
   original token.

7. **peinit MUST NOT drop its SYSTEM identity.** PID 1 runs as
   SYSTEM for the lifetime of the system.

8. **Identity MUST be deterministic.** Every service runs with a
   known identity. `SYSTEM` must be explicitly declared. Empty
   defaults to `LocalService`. The dangerous case (running as
   SYSTEM) is never implicit.

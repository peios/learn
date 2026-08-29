---
title: Security Invariants
description: The properties peinit does not violate, and the code paths that make each of them structural.
---

Properties peinit does not violate.

**1. peinit does not grant privileges it was not asked to grant.**
`RequiredPrivileges` is subtractive. peinit removes privileges and never
adds one — there is no code path that constructs anything but a removal
(§4.5).

**2. peinit does not bypass AccessCheck for control operations.** Every
control command reaches a check against the appropriate descriptor.
There is no backdoor, no override flag, and no "trust localhost". Every
command on a submitted job, on either socket, is checked against the
job's own descriptor — the submitter included, and the job identity
excluded unless the descriptor says otherwise (§8.5).

**3. peinit does not expose one service's state to another without
access control.** `list` returns only what the caller may query, and
`status` is checked per service; `job-list` and `job-status` are
checked per job (§10.2).

**4. peinit records every access denial.** A failed AccessCheck produces
an `access.denied` event — `job.access_denied` for a job — carrying
the caller's SID, the target, the requested right by name, and the
access bits requested and granted. Silent denial is not acceptable.

**5. The control descriptor, the ServiceSecurity descriptors and the
per-job descriptors are the only policy inputs for runtime access
control.** peinit consults no configuration file, no environment
variable and no hardcoded principal list. The only inputs to
AccessCheck are those descriptors — the first two sourced from the
registry with a compiled-in default, the third fixed at submission from
the submitter's SID or the SDDL it supplied. Who may *submit* is not a
policy input at all: it is the jobs socket's file descriptor, decided by
the filesystem before peinit sees the connection.

**6. peinit does not share its SYSTEM token.** It opens its own token
query-only, as a template, and never installs it on a child. Even an
`Identity=SYSTEM` service gets a separately minted token.

**7. peinit does not drop its SYSTEM identity.** PID 1 runs as SYSTEM
for the lifetime of the system. Only the forked child installs a token;
peinit never installs one on itself.

**8. Identity is deterministic, and the dangerous case is never
implicit.** Every service runs with a known identity. `SYSTEM` has to be
declared explicitly; an absent or empty `Identity` means `LocalService`.

The declaration logic upholds the eighth: an empty value resolves to
`LocalService`, and `SYSTEM` is reached only by naming it. What a
service actually receives depends on materialisation, and while the
authd client returns a minted SYSTEM token for every identity (§4.3), a
service that declared nothing runs on one.

**9. A submitted job runs only as an identity the kernel verified its
submitter could convey.** There is no identity field, no route from a
plain descriptor to a job identity, and no token opened through a
PID or descriptor the submitter named. The job identity is the
connecting process's own primary — reached through the kernel's handle
on that process — or the token the kernel attached to the message after
running the impersonation gates with the submitter as installer.
peinit never re-derives that decision and never refuses a token for
who it names (§8.5).

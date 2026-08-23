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
There is no backdoor, no override flag, and no "trust localhost".

**3. peinit does not expose one service's state to another without
access control.** `list` returns only what the caller may query, and
`status` is checked per service (§10.2).

**4. peinit records every access denial.** A failed AccessCheck produces
an `access.denied` event carrying the caller's SID, the target, the
requested right by name, and the access bits requested and granted.
Silent denial is not acceptable.

**5. The control descriptor and the ServiceSecurity descriptors are the
only policy inputs for runtime access control.** peinit consults no
configuration file, no environment variable and no hardcoded principal
list. The only inputs to AccessCheck are those two descriptors, sourced
from the registry with a compiled-in default.

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

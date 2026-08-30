---
title: The SYSTEM Path
description: peinit mints SYSTEM tokens itself, which is what breaks the bootstrap circle for registryd, lpsd, authd and eventd.
---

For `Identity=SYSTEM`, peinit mints a token itself. This is what breaks
the bootstrap circle: registryd, lpsd, authd and eventd all need tokens,
and authd — the thing that mints tokens — is one of them.

## Minting

peinit reads its own token as a template and builds a new **primary**
token carrying the same identity: user SID `S-1-5-18`, the same group
list, the same privilege set, the same integrity level. The mint
requires `SeCreateTokenPrivilege`, which the boot SYSTEM token carries;
the kernel refuses the call with `EPERM` otherwise.

Two details of the copy matter.

**The logon session comes from the token's statistics.** peinit takes
the `auth_id` from the source token's `TokenStatistics` — not from the
independent `interactivity_scope` field, and not from a hard-coded
well-known SYSTEM LUID. The minted token therefore stays associated
with the real SYSTEM logon session peinit was given at boot, while
carrying its own interactivity scope, which is zero for a platform
service. Substituting either of the other two values would associate
platform services with a session that does not exist.

**The logon SID group is dropped from the copy.** The kernel re-appends
the session's logon SID when it creates the token, and rejects a create
whose group list already contains it. So peinit filters that group out
of the template before building.

**Two groups are added that the template does not carry.** The
per-service SID (§4.4), which is what keeps platform daemons
distinguishable while they all run as SYSTEM; and the Service group
`S-1-5-6`, which every token authd mints for a service logon carries by
derivation from the logon type.

The second is load-bearing rather than cosmetic. `S-1-5-6` is the
grantee on anything reachable by services as a class — peinit's own
notification socket first among them (§10.5) — so a SYSTEM service
minted here without it would be unable to report itself ready, while an
otherwise identical service on an authd-minted token could. A service is
no less a service for having been started before the authority was.

peinit also asserts that its own token is a primary token and that its
user SID really is `S-1-5-18` before minting, and fails the start with a
message naming what it found otherwise. PID 1 minting from something
that is not the boot SYSTEM token is not a situation to proceed from.

The minted token is fully independent. The privilege restriction that
follows (§4.5) operates on it alone and cannot affect peinit's own.

> [!NOTE]
> Minting is an interim mechanism. The intended model is for peinit to
> *derive* the token from its own handle, through a KACS
> duplicate-with-additions operation — kernel-attested as a descendant
> of peinit's real token, and requiring no token-minting privilege at
> all. That operation does not exist in KACS yet, so peinit mints.

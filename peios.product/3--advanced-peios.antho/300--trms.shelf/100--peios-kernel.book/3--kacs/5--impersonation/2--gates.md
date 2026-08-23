---
title: Impersonation Gates
description: The two independent checks that decide whether an impersonation proceeds at the level asked for — the identity gate and the integrity ceiling.
---

When a server thread attempts to impersonate a client's token, two
independent checks decide whether it proceeds at the requested level.
Both have to pass. If either fails the effective level is reduced to
Identification — the movement is only ever downward.

Both gates are evaluated against the server's **primary token**
(`real_cred`), never its effective token. A server already
impersonating another client has its gates judged against its own
service identity, so a previous impersonation cannot influence the
next one.

## The identity gate

The identity gate asks whether this server may impersonate this
particular user's identity. Impersonation at Impersonation or
Delegation level is permitted if either of two conditions holds.

**Same user, same restriction status** — the server's primary token
and the client's token carry the same user SID, and both are
restricted or both unrestricted.

**`SeImpersonatePrivilege`** — the server's primary token holds it,
enabled.

If neither holds, the level is **silently capped to Identification**.
No error is returned: the call succeeds, and the resulting token is
merely at Identification level.

There is one hard denial. A **restricted** server impersonating an
**unrestricted** client of the same user is rejected outright with
`-EPERM` rather than capped, because that is precisely how a sandboxed
process would escape by impersonating its parent's unrestricted token.
The reverse direction, unrestricted server to restricted client, is a
harmless downgrade and takes the ordinary cap-to-Identification path.

MS-DTYP includes a third condition — an origin LogonSession check
letting the session that created a token impersonate it without the
privilege. KACS drops it. A service needing to impersonate a different
user holds `SeImpersonatePrivilege`, and there are no hidden paths.

## The integrity ceiling

The integrity ceiling asks whether the client's token sits at an
integrity level the server is allowed to assume. To act at
Impersonation or Delegation level, the client token's integrity level
has to be less than or equal to the server primary token's. A
Medium-integrity server can impersonate Low or Medium clients; against
a High-integrity client the level caps to Identification.

The installed token may keep the client's literal integrity label as
identity metadata after the cap, but that preserved label authorizes
nothing, because Identification-level tokens are barred from
AccessCheck entirely.

The ceiling exists because MIC evaluates the *effective* token's
integrity level for tokens that can act. Without it, a server could
impersonate a higher-integrity token and gain write access to
higher-integrity objects — integrity escalation through impersonation.

The ceiling is enforced unconditionally, regardless of privilege.
`SeImpersonatePrivilege` bypasses the identity gate and never the
ceiling. MS-DTYP allows the privilege to bypass every check including
this one; KACS does not, because `mandatory_policy` is immutable here
(§3.2.2) and MIC is consequently a real boundary. Letting a privilege
punch through would give back exactly what that immutability buys.

## Composition

The two gates are independent, both are evaluated, and the effective
level is the minimum any constraint permits: start from the level the
client set on the socket, cap to Identification if the identity gate
fails, cap to Identification if the integrity ceiling fails, and the
result is the effective impersonation level.

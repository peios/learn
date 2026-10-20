---
title: Establishing What a Source Is
description: The authority establishes a connecting source's identity from the kernel, never from what the source says, and checks it against an allowlist.
---

The authority MUST establish a connecting source's identity **for
itself**, from the kernel, and MUST NOT take it from anything the source
sends.

## A source proves nothing

The mechanism worth recommending is that a source proves nothing at all,
because the init system already did.

Where the init system places a **service SID** in each service's token —
a SID derived from the service's name, which only the init system can
mint — the authority can:

1. take its list of permitted source names from its own configuration;
2. derive the service SID each of those names implies;
3. read the connecting peer's token and ask which of those SIDs it
   carries.

The resulting identity is assembled entirely from the authority's
configuration and the kernel. **Nothing is contributed by the process on
the other end.** There is no shared secret, nothing to provision,
nothing to rotate, and nothing to steal — the derivation is a pure
function of a name that only the init system can act on.

> [!NOTE]
> Mainline derives `S-1-5-80-<SHA-1 of the uppercased UTF-16LE service
> name>`, matching what the init system places in every service token.
> The derivation exists so that platform services — all running as
> SYSTEM — remain distinguishable from one another, which is exactly
> this problem.

## What is deliberately not checked

**That the peer is SYSTEM.** The service SID subsumes it: the user SID
could never distinguish one platform service from another, since they
all run as the same principal. Requiring SYSTEM as well would needlessly
forbid a future source running under a lesser account, which is a
direction worth keeping open.

## The allowlist

An authority MUST NOT accept a source it has not been configured to
accept.

An empty configuration MUST mean **no source may register**, not *any
source may*. An allowlist that fails open is not an allowlist. The
visible cost is that a system configured with no sources cannot
authenticate anyone, which is the correct way for that mistake to
present — loudly, at the first logon attempt, rather than silently at
the first compromise.

> [!NOTE]
> Mainline's allowlist is a registry key whose *subkey names* are the
> permitted source names, so enumerating that key answers "what may
> assert identity on this machine?" exactly, with no second list
> anywhere to drift out of step.

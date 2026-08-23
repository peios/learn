---
title: Private Hives
description: Hives invisible in the global namespace, reachable only through a scope GUID on the calling token — routing, lifecycle and registration rules.
---

A private hive is registered with the `RSI_HIVE_PRIVATE` flag and a
scope GUID. It is invisible in the global namespace and reachable only
by a thread whose token carries that scope GUID.

## Routing

Private hives are checked **before** global ones. For each scope GUID
on the calling thread's token, in the order the token carries them, LCS
looks for a private hive with the path's name and that scope. The first
match wins. Only if none matches is the global table consulted.

A private hive can therefore shadow a global one, and no name is exempt
— a thread with a private `Machine\` sees the private one. That is what
makes complete registry isolation possible for a container or a
sandbox without giving it a differently-named hive to notice.

`MaxScopeGUIDsPerToken`, default 8, bounds the per-syscall iteration
cost. Duplicate scope GUIDs on a token are rejected.

## Scope GUIDs on a token

Scope GUIDs reach a thread through the KACS token's LCS credential
extension: a versioned block in the token specification carrying the
thread's scope GUIDs and its private layer names (§5.3.5). It parses at
a fixed offset, rejects nil and duplicate GUIDs, and caps the count at
256 — a hard KACS limit, above the configurable LCS one. The
credentials propagate across fork, duplication and impersonation like
the rest of the token.

Attaching them is gated by `SeCreateTokenPrivilege`, because scope
GUIDs can only enter a token when the token is created. That is a
blanket privilege rather than a per-scope authorisation: a caller that
can create tokens at all can create one claiming any scope. Isolation
between private hives therefore rests on who may create tokens, not on
who owns a scope.

## Scope lifecycle

A scope GUID is an opaque 128-bit value with no lifecycle. LCS neither
creates nor tracks one; it only compares. A scope exists as long as
some private hive or some token references it, and when the last
reference goes it is simply a number nobody uses.

Nothing in the kernel generates scope GUIDs. Key GUIDs and token GUIDs
come from the kernel's UUIDv4 generator; scope GUIDs are supplied by
userspace, and choosing them unpredictably is userspace's
responsibility.

## Registration rules

Registration enforces more than the route-identity uniqueness of
§5.2.1:

- A hive's root GUID may not be nil, and the root GUIDs within one
  registration request must be distinct.
- A hive without the `RSI_HIVE_PRIVATE` flag may not carry a non-nil
  scope GUID.
- Unknown flag bits are rejected.
- Opening `/dev/pkm_registry` at all requires an **enabled**
  `SeTcbPrivilege`, checked in the device's `open()` handler
  (§5.8.2).

A private hive registered with an all-zero scope GUID is accepted. No
token can carry a nil scope GUID, so such a hive is registrable and
then permanently unroutable.

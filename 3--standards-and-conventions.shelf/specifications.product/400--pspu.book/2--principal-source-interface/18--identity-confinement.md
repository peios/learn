---
title: Identity Confinement
description: An assertion outside the source's registered domain is refused and the conversation terminated. No configuration lifts this.
---

**A source may assert only principals within its declared domain
(§2.10). No configuration lifts this.**

An authority MUST refuse an `Assertion` whose `user_sid` does not lie
within the domain the source registered for, and MUST terminate the
logon. It MUST apply the same test to a `QueryResult` (§2.15) and to the
`sid` of a `Changed` (§2.17).

## Containment

A principal SID lies within a domain when it is the domain's SID plus
**exactly one** relative identifier.

Exactly one, deliberately. `S-1-5-21-A-B-C-1000-1` is not a principal of
`S-1-5-21-A-B-C`, and admitting it would let a source that owns one
domain mint names in a nested namespace nobody agreed it owned. A domain
SID is likewise not a principal of itself.

## Why nothing lifts it

A source that could assert identities outside its domain could hand out
**another authority's principals** to anyone who satisfied *its*
credential check.

The concrete case: a local source holds no domain credential. If it were
unconfined, it could produce a domain administrator's identity for
anyone who knew a *local* password. The domain's own authority would
never be consulted and would have no way to know.

Confinement keeps a compromised source at "authority over its own
domain" — which is what it already was — rather than "authority over
everyone".

This is why identity scope and membership scope (§2.19) are separate
settings rather than one. They are different questions, and only one of
them has a legitimate exception.

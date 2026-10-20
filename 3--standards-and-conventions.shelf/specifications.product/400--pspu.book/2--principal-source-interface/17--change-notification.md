---
title: Change Notification
description: The unsolicited message that lets an authority cache name lookups safely, and what it deliberately does not carry.
---

An authority answering a name lookup for every process on the system
will cache. This is the message that lets it.

## Changed

`msg_type` = `0x8007`. Source to authority, on conversation `0`.
Unsolicited, and never answered.

| Field | Encoding | Limit |
|---|---|---|
| `scope` | `u8` | §2.B |
| `sid` | length-framed bytes (SID) | 68 bytes |

| `scope` | Name | Meaning |
|---|---|---|
| 1 | `All` | Everything this source holds may have changed. |
| 2 | `Object` | The object named by `sid` may have changed. |

`sid` is meaningful only for `Object`, and MUST be within the source's
declared domain (§2.18).

`Object` scope MUST be used for a **deletion** as well as a change, and
for a **creation** — an authority may be holding a cached `NotFound` for
a name that now exists.

## Obligations

A source declaring `PUSHES_CHANGES` (§2.8) MUST send `Changed` before,
or at the same time as, the altered answer becomes observable through
`Query`.

Sending it afterwards leaves a window in which the authority's cache and
the source disagree while both believe themselves current — which is
indistinguishable, from the authority's side, from the notification
never arriving.

A source MAY send `All` where it could have sent `Object`.
Over-invalidation costs a query; under-invalidation costs correctness.

An authority MUST accept `Changed` at any time after `Registered`,
including while conversations are open on the same connection, and MUST
NOT reply to it.

An authority MUST treat the loss of a source's connection as `All` for
that source. It does not know what changed while it was not listening.

A source declaring `PUSHES_CHANGES` SHOULD declare a non-zero
`entry_ttl` as well (§2.8). The two are not alternatives: the TTL is the
backstop against a notification that was never sent, or was sent and
failed to write. Declaring `PUSHES_CHANGES` with a TTL of zero means a
single lost notification leaves the authority holding a stale answer
until the connection drops — and a source that tolerated a failed
`Changed` write without tearing the connection down would have made that
outcome reachable, which is one of the reasons §2.6 makes a failed write
fatal.

## Sources that do not push

A source that does not declare `PUSHES_CHANGES` is conforming, and many
cannot: a remote directory has no way to tell this machine that an
account was renamed.

Such a source declares `entry_ttl` instead (§2.8), and an authority MUST
NOT hold its answers beyond it.

A source declaring **neither** has said it cannot support caching, and
an authority MUST NOT cache its answers at all. That is the safe reading
of silence, and it is what a source predating this message says by
omission.

> [!NOTE]
> The alternative default — cache anything not explicitly forbidden —
> would make a source written against an older revision silently serve
> stale identity, which is the one class of staleness that decides
> access.

An authority that does not cache at all satisfies this section
trivially, and is conforming. The obligations here bind what an
authority may hold, not whether it must hold anything.

## What this does not carry

`Changed` says that something changed. It does not say what it changed
to.

Carrying the new value would make this a second, unsolicited path by
which a source could assert identity — one arriving outside any
conversation, with no key to check it against, and no logon in progress
to refuse. An authority that believed it would have accepted an identity
assertion it never asked for.

The authority discards what it holds and asks again through `Query`,
where every scope rule in §2.18 to §2.20 applies.

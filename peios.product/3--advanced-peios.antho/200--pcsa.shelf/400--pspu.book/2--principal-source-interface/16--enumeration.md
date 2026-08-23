---
title: Enumeration
description: Paging through a source's principals or a large group's members, with cursors that belong to the source.
---

`Query` asks about objects the authority can already name. Enumeration
asks a source to produce them: to fill a POSIX `passwd` or `group`
table, or to page through a group whose membership will not fit in one
answer.

**A source is never required to enumerate.** A source that declines is
fully conforming, and this section exists as much to make declining safe
as to make enumerating possible.

## EnumerateSource

`msg_type` = `0x0006`. Authority to source. Opens a conversation.

| Field | Encoding | Limit |
|---|---|---|
| `kind` | `u8` | PGSS §2.B |
| `fields` | `u32` | PGSS §2.B |
| `of` | length-framed key entry (§2.15) | |
| `cursor` | length-framed bytes | 256 bytes |

`kind` MUST NOT be `Any`.

An empty `of` enumerates every object of `kind` the source holds. A
non-empty `of` MUST name a group, and enumerates that group's members.

`cursor` is empty on the first request, and otherwise carries the `next`
from the source's immediately preceding reply.

## EnumerateResult

`msg_type` = `0x8006`. Source to authority. Terminal.

| Field | Encoding | Limit |
|---|---|---|
| `outcome` | `u8` | §2.B |
| `entries` | array of result entries (§2.15) | 256 |
| `next` | length-framed bytes | 256 bytes |

An empty `next` ends the enumeration. A non-empty `next` means there is
more, **even where `entries` is empty**.

A source MUST size a page against the smaller of this chapter's message
ceiling and PGSS Logon's, because the authority re-encodes what it
returns into the latter (§2.A). Neither the 256-entry bound nor the
message ceiling here prevents a page nobody can deliver.

A source that will not enumerate replies `Refused`, with `entries` and
`next` empty. An authority MUST record it as a source that did not
contribute, and MUST NOT retry it for the remainder of that enumeration
— across pages as well as within one (PGSS §2.17).

`Refused` and an empty `Found` are **different answers and MUST NOT be
conflated**. `Found` with `entries` and `next` both empty says *there
are none*: the group exists and has no recorded members, or the source
holds no objects of that kind. `Refused` says *this source is not
answering*. A source that returns an empty `Found` where it means the
second has told the authority a falsehood it cannot detect, and the
authority will go on asking it — the non-retry rule above has nothing to
attach to.

The cases most often got wrong, all of which are `Refused` and not an
empty `Found`: a group whose membership the source will not expose, a
key that names an object the source does not hold, a key that names a
principal where a group was required, and a cursor the source can no
longer honour.

## Cursors belong to the source

A cursor is **opaque to the authority**. The authority MUST NOT
construct, parse or modify one; it relays what it was given.

A source MAY encode anything into a cursor, and MAY refuse one it no
longer honours — a store rewritten underneath a half-finished walk is
the ordinary case, not an exceptional one. A refused cursor is
`Refused`, and the authority MUST NOT restart the enumeration on the
source's behalf.

> [!NOTE]
> Restarting would turn a store edit during a `getent passwd` into an
> unbounded loop over a source that never finishes. Reporting an
> incomplete enumeration is the honest outcome, and PGSS §2.17 requires
> the authority to say so.

A source MUST NOT assume a cursor comes back on the same conversation,
or on the same connection, and MUST NOT hold per-cursor state it is
unwilling to discard.

The authority's own cursor, the one it hands its client, is its to
construct — PGSS §2.17 requires it to reject one it did not issue, which
it can only do for a cursor it made. A source's cursor travels inside
it, not as it.

## Why members are here and not only in Query

`MEMBERS` is a field of `Query` (§2.15), so the common case — a small
group, whose members fit alongside the rest of the record — costs one
exchange.

A group whose membership will not fit is reported through PGSS Logon's
`TooLarge` (PGSS §2.16), and this is where the caller is sent. Paging a
membership through the mechanism that already pages is cheaper than a
third message, and considerably cheaper than the alternative of a
partial member list, which is a wrong answer rather than a smaller one.

## Enumeration is not existence

An authority MUST NOT use enumeration to determine whether a principal
exists, and MUST NOT infer from a source declining to enumerate that the
source holds nothing.

A directory-backed source able to answer any single question while quite
unable to answer all of them is the expected case, not a degraded one.

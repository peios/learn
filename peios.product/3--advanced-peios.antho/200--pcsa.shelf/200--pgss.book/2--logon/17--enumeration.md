---
title: Enumeration
description: Walking every principal or every member of a large group, with a cursor and no completeness guarantee.
---

`Lookup` answers about one object that a caller can already name.
Enumeration answers when it cannot: walking every principal on the
system, or every member of a group too large for one reply.

## Enumerate

`msg_type` = `0x0011`. Client to authority.

| Field | Encoding | Limit |
|---|---|---|
| `tag` | `u32` | §2.14 |
| `kind` | `u8` | §2.B |
| `fields` | `u32` | §2.B |
| `of_key_type` | `u8` | §2.B |
| `of_name` | string | 256 bytes |
| `of_sid` | length-framed bytes (SID) | 68 bytes |
| `of_unix_id` | `u32` | |
| `cursor` | length-framed bytes | 256 bytes |

`kind` MUST NOT be `Any`. A caller enumerating is filling a `passwd` or
a `group` table, and the two are separate.

### of

Where `of_key_type` is zero, the request enumerates every object of
`kind` that the authority knows.

Where it is non-zero, the named object MUST be a group, and the request
enumerates **that group's members**. This is the continuation path for a
`MEMBERS` field withheld as `TooLarge` (§2.16): the same answer, paged.
An authority that withholds `MEMBERS` as `TooLarge` MUST serve this
mode, since there is otherwise no way to obtain what it said existed.

> [!NOTE]
> Members are a field of `Lookup` for the common case and a mode of
> `Enumerate` for the large one, rather than a message of their own. The
> field keeps `getgrnam` to one round trip where the group is small,
> which is nearly always; this keeps the large case correct without a
> third request type or a partial member list, which would be worse than
> no list at all.

### cursor

Empty on the first request. On a continuation it MUST be the `next`
returned by the immediately preceding reply.

A cursor is **opaque**. A client MUST NOT construct, parse or modify
one, and MUST NOT present one to a different authority or after
reconnecting.

An authority MUST reject a cursor it did not issue, or one it can no
longer honour, with `Malformed` (§2.18). It MUST NOT silently restart
the enumeration, and MUST NOT answer with an empty page and an empty
`next`: the first hands the caller a second copy of the beginning under
the impression it is continuing, and the second reports a truncated walk
as a complete one.

## EnumerateReply

`msg_type` = `0x8011`. Authority to client.

| Field | Encoding | Limit |
|---|---|---|
| `tag` | `u32` | §2.14 |
| `outcome` | `u8` | §2.B |
| `entries` | array of entries | 256 |
| `next` | length-framed bytes | 256 bytes |
| `incomplete` | array of strings | 32 |

An entry is a length-framed structure carrying the same fields as a
successful `LookupReply` (§2.16), from `sid` through `values`.

An empty `next` means the enumeration is complete. A non-empty `next`
means there is more, **even if `entries` was empty** — an authority may
return a short or empty page while working through a source.

A client MUST continue until `next` is empty. A client MUST NOT infer
completion from an empty page.

A client MUST NOT report an enumeration as complete when it stopped for
any other reason. A transport failure, a timeout, or an outcome other
than `Found` mid-walk is a truncated enumeration, and a client that
presents it to its caller as the end of the list has manufactured an
empty system out of an outage — the same error §2.18 forbids on a single
lookup, at a scale where nothing records that it happened.

## incomplete

Each string names a source that did not contribute: because it declined
to enumerate, or because it could not be reached.

An authority MUST list every such source. A client displaying an
enumeration SHOULD say that it is partial, and MUST NOT discard the list
without doing so.

> [!NOTE]
> A short list that looks complete is the failure this field exists to
> prevent. An administrator reading an account listing has no way to
> tell a machine with four principals from a machine whose directory did
> not answer, and the difference decides whether they are looking at the
> whole picture.

## No completeness guarantee

An authority MUST NOT be required to enumerate.

A source may hold more principals than a reply, a page, or an
administrator's patience can carry, and a source backed by a remote
directory may be able to answer any single question while being quite
unable to answer all of them. `incomplete` is the honest outcome, not a
degraded one.

A caller MUST NOT treat enumeration as a way to test whether a principal
exists. `Lookup` answers that, exactly, at any scale.

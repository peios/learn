---
title: Groups and Membership
description: Listing, creating and deleting local groups, and putting principals in groups — local, BUILTIN or any other — and setting a principal's primary group.
---

## GroupList

`msg_type` = `0x000a`. Empty body. Answered with `Groups`.

## Groups

`msg_type` = `0x8007`. Every **local** group in the store, as an array of
at most 4096 length-framed entries:

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes |
| `rid` | `u32` |
| `unix_id` | `u32`: its effective Unix ID (§10.2) |
| `sid` | SID |
| `members` | `u32`: how many principals list it |

The well-known groups are not in it: the store holds none of them as
objects (§10.2). `members` counts listed memberships, not principals
whose primary group it is; the identity socket's `MEMBERS` counts both
(PGSS §2.16).

## GroupCreate

`msg_type` = `0x000b`. Body: `name`. Creates a local group, with the
store's next RID. Answered with `Created` carrying it.

A store daemon MUST refuse a name it already holds, a principal's or a
group's, as `Exists`, and applies the same rules to a group's name as to
a principal's (§10.5).

## GroupDelete

`msg_type` = `0x000c`. Body: `name`, a local group's. Deletes it.
Answered with `Done`.

A store daemon MUST refuse, as `Invalid`, deleting a group any principal
lists or has as its primary group: a principal would be left in a group
that no longer exists. A client removes the members first.

A store daemon MUST answer `NotFound` where it holds no local group by
`name`, a well-known group's name included.

> [!NOTE]
> `lpsd` up to 0.0.22 answers `Internal` there, not `NotFound`.

## GroupAdd and GroupRemove

`GroupAdd`, `msg_type` = `0x0008`, puts a principal in a group;
`GroupRemove`, `msg_type` = `0x0009`, takes it out. Both are answered
with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes: the principal |
| `group` | string, 256 bytes: the group as written (§10.2) |

`name` MUST name a principal: groups do not nest, and a store daemon MUST
answer `NotFound` for a group's name there.

`group` MAY name a local group, a `BUILTIN` group, or any group by its
SID. A membership of a `BUILTIN` group is recorded here on the machine's
behalf, and asserted at sign-in under PSI's membership-scope exception
(§2.19); it is how a principal becomes an administrator. A membership of
a group in another domain is recorded as given.

Both are idempotent: adding a membership already held, or removing one
not held, is `Done` and changes nothing. A principal MAY be listed in at
most 128 groups; a store daemon MUST refuse a 129th as `Invalid`.

Removing a principal from `BUILTIN\Administrators` is refused if it is
the last enabled one there (§10.5).

A store daemon MUST answer `NotFound` for a `group` that names nothing it
can resolve.

> [!NOTE]
> `lpsd` up to 0.0.22 answers `Internal` there, not `NotFound`.

## SetPrimaryGroup

`msg_type` = `0x000e`. Body: as `GroupAdd`. Makes `group` the principal's
primary group: the one it projects to as its POSIX group ID. Answered
with `Done`.

A primary group is a membership (§2.13): the principal is in it whether
or not it is also listed.

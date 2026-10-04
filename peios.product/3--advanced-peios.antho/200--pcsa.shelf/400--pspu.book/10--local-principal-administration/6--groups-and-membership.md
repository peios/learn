---
title: Groups and Membership
description: Listing, creating, renaming, describing and deleting local groups, and putting principals in groups — local, BUILTIN or any other — and setting a principal's primary group.
---

## GroupList

`msg_type` = `0x000a`. Empty body. Answered with `Groups`.

## Groups

`msg_type` = `0x8007`. Every **local** group in the store, as an array of
at most 4096 length-framed entries:

| Field | Encoding | Default if absent |
|---|---|---|
| `name` | string, 256 bytes | |
| `rid` | `u32` | |
| `unix_id` | `u32`: its effective Unix ID (§10.2) | |
| `sid` | SID | |
| `members` | `u32`: how many principals list it | |
| `description` | string, 1024 bytes | empty |

The well-known groups are not in it: the store holds none of them as
objects (§10.2). `members` counts listed memberships, not principals
whose primary group it is; the identity socket's `MEMBERS` counts both
(PGSS §2.16).

A group's **description** says what it is for, on one line, for a person
to read; empty is none. Anyone may read it, on the identity socket's
`DESCRIPTION` (PGSS §2.16), where a store daemon that is a principal
source answers it.

## GroupCreate

`msg_type` = `0x000b`. Creates a local group, with the store's next RID.
Answered with `Created` carrying it.

| Field | Encoding | Default if absent |
|---|---|---|
| `name` | string, 256 bytes | |
| `description` | string, 1024 bytes | empty |

A store daemon MUST refuse a name it already holds, a principal's or a
group's, as `Exists`, and applies the same rules to a group's name as to
a principal's (§10.5). It MAY refuse a description it will not keep as
`Invalid`; on Peios one may hold no control characters, and is kept with
the spaces at its ends removed.

A store daemon that predates `description` ignores it, and makes the
group with none, as `Add` describes (§10.5).

## GroupRename

`msg_type` = `0x0017`. Body: `name`, a local group's, then `new_name`,
as `Rename` (§10.5). Changes what the group is called. Answered with
`Done`.

Its SID, RID and Unix ID stay, and so does every membership of it, since
a membership names the group by SID. A store daemon MUST answer
`NotFound` where it holds no local group by `name`, and refuses
`new_name` as `Rename` does.

## GroupDescribe

`msg_type` = `0x0018`. Sets a local group's description. Answered with
`Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes: a local group's |
| `description` | string, 1024 bytes; empty clears it |

A store daemon MUST answer `NotFound` where it holds no local group by
`name`. The well-known groups' descriptions are the authority's, and
cannot be set here.

## GroupDelete

`msg_type` = `0x000c`. Body: `name`, a local group's. Deletes it.
Answered with `Done`.

A store daemon MUST refuse, as `Invalid`, deleting a group any principal
lists or has as its primary group: a principal would be left in a group
that no longer exists. A client removes the members first.

A store daemon MUST answer `NotFound` where it holds no local group by
`name`, a well-known group's name included.

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

## SetPrimaryGroup

`msg_type` = `0x000e`. Body: as `GroupAdd`. Makes `group` the principal's
primary group: the one it projects to as its POSIX group ID. Answered
with `Done`.

A primary group is a membership (§2.13): the principal is in it whether
or not it is also listed.

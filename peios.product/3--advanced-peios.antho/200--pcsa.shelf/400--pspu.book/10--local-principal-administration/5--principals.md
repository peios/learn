---
title: Principals
description: Listing the store's principals, one in full, the store's domain, and creating, deleting, enabling, disabling and changing a principal.
---

Every request naming a principal names it by `name`, a string of at most
256 bytes, matched without regard to case. A store daemon MUST answer
`NotFound` (§10.9) for a name it holds no principal by.

## List

`msg_type` = `0x0001`. Empty body. Answered with `Principals`.

## Principals

`msg_type` = `0x8001`. Every principal in the store, as an array of at
most 4096 length-framed entries:

| Field | Encoding | Default if absent |
|---|---|---|
| `name` | string, 256 bytes | |
| `rid` | `u32` | |
| `enabled` | boolean | |
| `groups` | `u32`: how many groups it is listed in | |
| `unix_id` | `u32`: its effective Unix ID (§10.2) | `0` |

`groups` counts listed memberships only, not the primary group.

## Show

`msg_type` = `0x0002`. Body: `name`. Answered with `Principal`.

## Principal

`msg_type` = `0x8002`. One principal in full:

| Field | Encoding | Default if absent |
|---|---|---|
| `name` | string, 256 bytes | |
| `rid` | `u32` | |
| `enabled` | boolean | |
| `sid` | SID | |
| `groups` | array of at most 128 group references | |
| `unix_id` | `u32`: effective | `0` |
| `primary_group` | one length-framed group reference | an empty reference |
| `home` | string, 4096 bytes | empty |
| `shell` | string, 4096 bytes | empty |
| `display_name` | string, 256 bytes | empty |
| `claims` | array of at most 64 claims (§10.4) | none |

A **group reference** is a length-framed structure:

| Field | Encoding | Default if absent |
|---|---|---|
| `sid` | SID | |
| `name` | string, 256 bytes: what this machine calls the group | empty |
| `unix_id` | `u32`: its effective Unix ID, or zero | `0` |

The store daemon names each group, a well-known one included, and gives
its number where it knows it, so a client never builds a SID or resolves
a name itself. An empty `name` means the store daemon knows no name for
the SID; zero means it cannot say the number.

## Domain

`msg_type` = `0x0003`. Empty body. Answered with `DomainIs`.

## DomainIs

`msg_type` = `0x8003`. Body: `sid`, the store's domain SID (§10.2).

`Domain` is the smallest request there is, changes nothing, and is
refused to anyone who may not administer the store (§10.3). A client MAY
send it to find out whether its caller may administer the store, before
offering to change anything.

## Add

`msg_type` = `0x0004`. Creates a principal. Answered with `Created`
carrying its RID.

| Field | Encoding | Default if absent |
|---|---|---|
| `name` | string, 256 bytes | |
| `credential_kind` | `u8`: `0` none, `1` a password | |
| `secret` | byte string, 4096 bytes | |
| `enabled` | boolean | |
| `groups` | array of at most 128 length-framed strings: groups as written (§10.2) | |
| `permitted_logon_types` | `u32` | `0`, not stated |

`credential_kind` says plainly whether the principal has a password,
rather than an empty `secret` meaning none, so that a client cannot make
a principal that needs no credential by accident. `secret` is present
either way, and empty for `0`. A store daemon MUST refuse an empty
`secret` with kind `1` as `Invalid`, and MUST refuse a kind it does not
know.

A principal made with kind `0` has the credential policy `NoCredential`
(§10.8): it signs in with nothing collected. One made with kind `1` has
the policy `Password`.

`permitted_logon_types` is the set of PGSS §2.16's, as PSI carries it
(§2.13). Zero is *not stated*, which the authority reads as its default:
every kind of sign-in a person could use, and never a service sign-in.

The principal gets the store's next RID, a home directory, a shell and a
primary group the store daemon chooses (on Peios, `/home/<name>`,
`/bin/sh` and `Authenticated Users`). A client changes them afterwards
with `SetProfile` and `SetPrimaryGroup`.

A store daemon MUST refuse a name it already holds, a principal's or a
local group's, as `Exists`, and a name it will not accept as `Invalid`
with the reason. Which names it accepts is its own. On Peios a name is 1
to 256 bytes of printable ASCII, may not contain `@ \ / : ,`, and may
not be a well-known group's name.

## Remove

`msg_type` = `0x0005`. Body: `name`. Deletes the principal. Answered with
`Done`.

Its RID is not reissued, so its SID keeps appearing in the descriptors of
whatever it owned, naming nobody. A client SHOULD say so before removing
one, and SHOULD offer disabling instead.

## SetEnabled

`msg_type` = `0x0006`. Body: `name`, then `enabled`, a boolean. Answered
with `Done`. A disabled principal keeps everything, and cannot sign in.

## SetPassword

`msg_type` = `0x0007`. Body: `name`, then `secret`, a byte string of at
most 4096 bytes, never empty. Sets the principal's password. Answered
with `Done`.

It does not change the principal's credential policy (§10.8). A
principal whose policy accepts no password is not given one by this
request: a client that means the password to be used MUST also send
`CredentialPolicy`.

## SetProfile

`msg_type` = `0x000d`. Changes part of a principal's profile, leaving the
rest alone. Answered with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes |
| `home` | optional string (§10.4), 4096 bytes |
| `shell` | optional string, 4096 bytes |
| `display_name` | optional string, 256 bytes |

An absent field is left as it is. A present empty `display_name` clears
it. A store daemon MAY refuse a value it will not accept as `Invalid`;
on Peios `home` and `shell` must be absolute paths.

## Last administrator

A store daemon MUST refuse, as `Invalid`, a request that would leave the
store with no enabled principal in `BUILTIN\Administrators`: removing or
disabling the last one, or removing the last one from that group
(§10.6). A machine left so has nobody to administer it.

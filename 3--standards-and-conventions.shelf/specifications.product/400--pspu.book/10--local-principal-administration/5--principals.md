---
title: Principals
description: Listing the store's principals, one in full, the store's domain, and creating, deleting, renaming, enabling, disabling and changing a principal.
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
| `permitted_logon_types` | `u32`, as on `Add` | `0`, not stated |
| `credential_policy` | `u8` (§10.8) | not said |

`credential_policy` is closed, as §10.8 says: a client MUST treat a
value it does not know as a reply it cannot read. A client given no
`credential_policy` MUST NOT show one; the store daemon did not say.

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
| `primary_group` | optional string (§10.4), 256 bytes: a group as written | absent |
| `home` | optional string, 4096 bytes | absent |
| `shell` | optional string, 4096 bytes | absent |
| `display_name` | optional string, 256 bytes | absent |

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

The principal gets the store's next RID. Where `primary_group`, `home`,
`shell` or `display_name` is absent, it gets what the store daemon
chooses (on Peios, `Authenticated Users`, `/home/<name>`, `/bin/sh` and
no display name). A present field is checked as `SetProfile` and
`SetPrimaryGroup` check it, and a store daemon MUST refuse the whole
request if it refuses any field, creating nothing: a principal is made
whole or not at all.

A store daemon that predates the last four fields ignores them, and
makes the principal with its own choices. A client cannot tell that
from the reply; one that must know reads the principal back with `Show`.

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

## Rename

`msg_type` = `0x0015`. Changes what a principal is called. Answered with
`Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes: the principal |
| `new_name` | string, 256 bytes: what it is to be called |

Its SID, RID and Unix ID stay, so everything that names it by SID, every
descriptor and every token already minted, still does. Its home directory
stays too: a store daemon MUST NOT change `home` on a rename. A client
that means the home directory to follow sends `SetProfile` as well.

A store daemon MUST refuse a `new_name` another principal or a local
group holds as `Exists`, and applies the rules for a name as `Add` does.
A `new_name` differing from the principal's name only in case is a
rename; one equal to it is `Done` and changes nothing.

## SetLogonTypes

`msg_type` = `0x0016`. Sets which kinds of sign-in a principal may be
used for. Answered with `Done`.

| Field | Encoding |
|---|---|
| `name` | string, 256 bytes |
| `permitted_logon_types` | `u32`, as on `Add` |

Zero returns the principal to *not stated*, the authority's default.
There is no value meaning "no sign-in at all"; a client disables the
principal for that. A store daemon MUST keep bits for logon types it
does not know as they are given, as it does on `Add`: the authority
checks the types it knows.

## Last administrator

A store daemon MUST refuse, as `Invalid`, a request that would leave the
store with no enabled principal in `BUILTIN\Administrators` who can sign
in: removing or disabling the last one, removing the last one from that
group (§10.6), setting the last one's `permitted_logon_types` to a
set that permits none of interactive, remote interactive or network
sign-in, or leaving the last one nothing to sign in with (§10.8): a
`CredentialPolicy` it would not have something to sign in with under,
or a `KeyRemove` of the last key it signs in with. A machine left so
has nobody to administer it.

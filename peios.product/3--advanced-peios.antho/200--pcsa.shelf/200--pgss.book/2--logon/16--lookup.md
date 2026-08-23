---
title: Lookup
description: One request that answers every question a name resolver asks — keys, fields, memberships, and the present/withheld distinction.
---

One request answers every question a name resolver asks.

## Lookup

`msg_type` = `0x0010`. Client to authority.

| Field | Encoding | Limit |
|---|---|---|
| `tag` | `u32` | §2.14 |
| `key_type` | `u8` | §2.B |
| `name` | string | 256 bytes |
| `sid` | length-framed bytes (SID) | 68 bytes |
| `unix_id` | `u32` | |
| `kind` | `u8` | §2.B |
| `fields` | `u32` | §2.B |

Exactly one of `name`, `sid` and `unix_id` is meaningful, selected by
`key_type`. An encoder MUST leave the others empty or zero, and a
decoder MUST ignore them.

### key_type

| Value | Name | Answers |
|---|---|---|
| 1 | `Name` | `getpwnam`, `getgrnam` |
| 2 | `Sid` | Rendering a security descriptor |
| 3 | `UnixId` | `getpwuid`, `getgrgid` |

`UnixId` is a key even though **no source is ever asked one**. An
authority converts the number to a source and a relative identifier by
the range arithmetic it assigned, and asks that source by relative
identifier or by SID.

A source therefore never receives an absolute number here, exactly as it
never receives one during a logon. The property that made the authority
the only possible answerer (§2.13) is the same property that keeps this
side of it confined.

### kind

| Value | Name |
|---|---|
| 0 | `Any` |
| 1 | `Principal` |
| 2 | `Group` |

A request for `Principal` MUST NOT be answered with a group, and a
request for `Group` MUST NOT be answered with a principal. Where the key
matches only an object of the other kind, the outcome is `NotFound`
(§2.18).

An authority MUST establish this for itself. Where the object came from
a source, the authority MUST check the kind it received against the kind
that was asked for, rather than relaying the source's answer and letting
the client discover the mismatch.

> [!NOTE]
> POSIX keeps users and groups in separate namespaces, so `getpwnam` and
> `getgrnam` can be asked the same string and expect different objects.
> Carrying the kind on the request is what lets both be served correctly
> without requiring an authority to forbid the collision.

### fields

A bitmask of the attributes the reply should carry. Identity is not
among them: every successful reply carries the SID, the canonical
qualified name, and the kind actually found, and a client cannot decline
them.

| Bit | Name | Value encoding |
|---|---|---|
| 0 | `UNIX_ID` | `u32` |
| 1 | `PRIMARY_GROUP` | reference |
| 2 | `HOME` | string, 4096 bytes |
| 3 | `SHELL` | string, 4096 bytes |
| 4 | `DISPLAY_NAME` | string, 256 bytes |
| 5 | `GROUPS` | array of references, 128 |
| 6 | `MEMBERS` | array of references, 256 |
| 7 | `CLAIMS` | array of claim entries, 64 |
| 8 | `ENABLED` | `u8` |

An authority MUST ignore a bit it does not implement, and MUST NOT
report it (below). Claim entries use the claim attribute format PCDS
§5.9 specifies.

> [!NOTE]
> Field bits are the one place in this chapter where an enumeration may
> grow without a version bump (§2.6). It is safe here, and only here,
> because the reply says which fields it is answering: an older
> authority ignoring a newer bit is reported as not implementing it,
> rather than silently omitting something a client believed it had asked
> for.

Requesting only what is wanted is not primarily a bandwidth measure — a
`getpwuid` wants nearly every field anyway. It matters for the caller
that resolves a dozen SIDs to render a security descriptor and wants
only names, and it is the seam at which an authority can restrict
individual fields without restricting the socket (§2.14).

## LookupReply

`msg_type` = `0x8010`. Authority to client.

| Field | Encoding | Limit |
|---|---|---|
| `tag` | `u32` | §2.14 |
| `outcome` | `u8` | §2.B |
| `sid` | length-framed bytes (SID) | 68 bytes |
| `qualified_name` | string | 512 bytes |
| `kind_found` | `u8` | §2.B |
| `present` | `u32` | §2.B |
| `withheld` | array of withheld entries | 32 |
| `values` | array of length-framed values | 32 |

Where `outcome` is not `Found`, everything after it MUST be empty or
zero, and a client MUST NOT read it.

`kind_found` MUST be `Principal` or `Group`, never `Any`.

### present, withheld and values

`values` holds one length-framed value for each bit set in `present`, in
**ascending bit order**. Each is length-framed so that a client can step
over a value whose field it does not recognise.

Every bit set in the request is in exactly one of three states:

- **set in `present`** — its value is in `values`;
- **listed in `withheld`** — with a reason, below;
- **in neither** — this authority does not implement the field.

The third state is a statement about the authority, not about the
object. An authority that implements a field MUST place every request
for it in one of the first two states, whatever happened underneath: a
field an authority supports but could not obtain is `Absent`,
`Declined`, `Restricted` or `TooLarge`, never silence. Reporting it as
neither would tell the client the authority cannot answer that question
at all, and a client is entitled to stop asking.

A withheld entry is a length-framed structure:

| Field | Encoding | Limit |
|---|---|---|
| `field` | `u32` | one bit, §2.B |
| `reason` | `u8` | §2.B |

| Reason | Meaning |
|---|---|
| `Absent` | The field has no value. |
| `Restricted` | The caller may not have this field. |
| `Declined` | The source will not produce it. |
| `TooLarge` | It exists and exceeds one reply. Use `Enumerate` (§2.17). |

Distinguishing these is the point of the structure. An empty member list
and a source that refuses to enumerate members are the same bytes to a
POSIX caller, and an administrator diagnosing a system needs to know
which one happened.

### References

`PRIMARY_GROUP`, `GROUPS` and `MEMBERS` carry references rather than
bare SIDs:

| Field | Encoding | Limit |
|---|---|---|
| `sid` | length-framed bytes (SID) | 68 bytes |
| `name` | string | 512 bytes |
| `unix_id` | `u32` | |

An empty `name` means the authority has no name for that SID; a
`unix_id` of **zero** means it has no number for it. Both are ordinary
answers for a SID belonging to no source on this machine.

Zero is the only encoding of "no number". An authority MUST NOT
substitute a POSIX identifier that a caller could mistake for a real
one — a projection onto `nobody` is a rendering decision belonging to
whatever produces a `passwd` record, and putting it on the wire
destroys the distinction the client needs in order to make it.

Carrying the name is what keeps the round-trip discipline below intact.
A reply of bare SIDs would make a single `getgrnam` into one request
plus one per member.

## Memberships

`GROUPS` on a principal is the membership question, and it is the
direction sources actually hold — the same one a logon uses. An
authority MUST answer it whenever it can answer anything about the
principal at all.

`MEMBERS` on a group is the reverse index, and it is not owed the same
guarantee.

An authority MUST return `MEMBERS` as withheld, rather than as an error
or an empty list, when it will not or cannot produce it:

- **`Declined`** where the source will not enumerate the group's
  members.
- **`TooLarge`** where the membership exceeds what one reply can carry.
- **`Absent`** where the group is not one that has recorded members at
  all.

That last case is not a limitation. A group's membership may be
**recorded** — held by a source, as a local group's is — or it may be a
**rule** an authority applies when it derives a token. Nothing records
who belongs to `Everyone`; an authority adds it to every token it mints.
Groups reflecting *how* a principal signed in are further still from a
recorded membership: they are properties of a logon rather than of a
principal, and the same principal is in one at a console and not over a
network.

An authority MUST report `Absent` for such a group rather than
manufacturing a list, and MUST NOT report `Declined`, which would
suggest an answer exists somewhere.

> [!NOTE]
> This asymmetry is deliberate and follows the shape of the data. "Which
> groups is this principal in" is answered by every source cheaply,
> because it is how memberships are stored. "Who is in this group" needs
> an index in the other direction, over a set that may be the whole of
> an organisation — historically the reliable way to make a directory
> server fall over from a filesystem listing.

## One round trip

An authority MUST be able to answer each of the following in a single
request:

| Caller wants | Request |
|---|---|
| A `passwd` record | `Lookup{key_type: UnixId or Name, kind: Principal, fields: UNIX_ID \| PRIMARY_GROUP \| HOME \| SHELL \| DISPLAY_NAME}` |
| A `group` record | `Lookup{key_type: UnixId or Name, kind: Group, fields: UNIX_ID \| MEMBERS}` |
| A principal's groups | `Lookup{key_type: Name, kind: Principal, fields: GROUPS}` |
| A name for a SID | `Lookup{key_type: Sid, kind: Any, fields: 0}` |

This is a design constraint on future revisions as much as a statement
about this one. A name resolver is called from every process on the
system, synchronously, and a field that cannot be fetched alongside the
record it belongs to turns one lookup into several.

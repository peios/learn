---
title: Query
description: Asking a source about a principal outside a logon — batching, relative identifiers, and the outcomes a query can return.
---

An authority serving PGSS Logon's identity lookup must be able to ask a
source about a principal outside a logon: to render a name for a SID, or
a POSIX record for a number.

A query is a conversation like any other. The authority allocates the
identifier, `Query` opens it, and one terminal message closes it.

## Query

`msg_type` = `0x0005`. Authority to source. Opens a conversation.

| Field | Encoding | Limit |
|---|---|---|
| `fields` | `u32` | PGSS §2.B |
| `keys` | array of key entries | 64 |

A key entry is a length-framed structure:

| Field | Encoding | Limit |
|---|---|---|
| `key_type` | `u8` | §2.B |
| `name` | string | 256 bytes |
| `sid` | length-framed bytes (SID) | 68 bytes |
| `relative_id` | `u32` | |
| `kind` | `u8` | PGSS §2.B |

Exactly one of `name`, `sid` and `relative_id` is meaningful, selected
by `key_type`. An encoder MUST leave the others empty or zero.

### Keys are never absolute

| Value | Name |
|---|---|
| 1 | `Name` |
| 2 | `Sid` |
| 3 | `RelativeId` |

**There is no key type carrying an absolute POSIX identifier**, and this
is the load-bearing property of the message.

PGSS Logon's lookup accepts one, because that is what `getpwuid` hands a
name resolver. The authority resolves it: it locates the range
containing the number, subtracts the base, and asks the owning source by
relative identifier.

A source is therefore never asked an absolute number, exactly as it
never asserts one during a logon (§2.20).

The reason is not that an absolute number would let a source escape its
range — it could not, because the authority refuses a relative
identifier at or past the count before adding anything to it (§2.20).
The reason is that the arithmetic must exist in exactly one place. A
source asked an absolute number would have to subtract its own base to
answer, which is the operation §2.20 forbids it, and an authority that
asked would have taught it that its stored numbers and the system's are
the same numbers. Every subsequent bug in that source would be an
off-by-a-base.

> [!NOTE]
> This is also why the authority is the only party that *can* answer a
> `getpwuid`. See PGSS §2.13.

### Batching

`keys` is an array so that an authority may ask several questions in one
exchange. An authority MAY send a single key, and one that always does
is conforming.

The array is here from the outset because adding it later would break
every source written against a single-key message. A source with a cheap
local store gains little; a source backed by a remote directory gains
the difference between one query and a hundred.

A source MUST answer every key it is sent, in order, and MUST NOT
reorder, merge or omit results. A source that cannot serve a whole batch
MUST refuse the conversation rather than answer part of it.

## QueryResult

`msg_type` = `0x8005`. Source to authority. Terminal.

| Field | Encoding | Limit |
|---|---|---|
| `results` | array of result entries | 64 |

One result per key, in the order the keys were sent.

A result entry is a length-framed structure:

| Field | Encoding | Limit |
|---|---|---|
| `outcome` | `u8` | §2.B |
| `sid` | length-framed bytes (SID) | 68 bytes |
| `canonical_name` | string | 256 bytes |
| `kind` | `u8` | PGSS §2.B |
| `present` | `u32` | PGSS §2.B |
| `withheld` | array of withheld entries | 32 |
| `values` | array of length-framed values | 32 |

Everything from `present` onward is PGSS §2.16's structure, unchanged —
the same reuse of message bodies as the interrogation phase (§2.5), and
for the same reason: an authority relaying a source's answer outward
should not have to translate it.

Where `outcome` is not `Found`, everything after it MUST be empty or
zero.

### canonical_name, not qualified

A source returns **its own spelling** of the name, as it does in an
`Assertion` (§2.13). It does not qualify it.

Qualification names which source answered, and a source cannot know what
it is called in another authority's search order. PGSS Logon requires a
qualified name on the way out (PGSS §2.15); producing it is the
authority's.

### Identifiers are relative

Every identifier in a result — a `UNIX_ID` field, a reference's
`unix_id` — is **relative**, exactly as in an `Assertion` (§2.20). A
source MUST NOT apply a base, and the authority rebases before the
number leaves it.

### Outcomes

A source may send only:

| Value | Name | Meaning |
|---|---|---|
| 1 | `Found` | The source holds this object. |
| 2 | `NotFound` | It does not. |
| 4 | `Refused` | It holds it and will not say so. |

A source MUST NOT send `Unavailable`: it is answering, so nothing was
unavailable to it. The authority produces that outcome when a source
does *not* answer (PGSS §2.18), and a source claiming it would let a
working source be recorded as a broken one.

A source MUST NOT send `Malformed` in a result. A message it cannot
parse is a `Refusal` for the whole conversation (§2.13).

> [!NOTE]
> `Refused` is how a source declines to expose a principal it holds —
> which §2.21 has always permitted. It is distinct from `NotFound`
> because the authority may consult another source on `NotFound`, and
> must not on `Refused`: the object was found, and the answer was no.

A `Refused` result is about the object, not about the caller, and an
authority MUST NOT relay it outward as PGSS Logon's `Refused` outcome,
which is reserved for a caller that may not make the request (PGSS
§2.18). What a source declining to expose an object means to a client is
the authority's to decide, and it is not "you lack permission".

A source that declared no `QUERIES` is a third case again. It has not
answered and cannot be asked, so an authority MUST NOT record it as
having answered `NotFound`: a source that was never consulted is not
evidence that an object does not exist, and PGSS §2.18 forbids reporting
`NotFound` on the strength of one. It contributes nothing to the search,
and §2.8 says what an authority should do about the configuration that
produced it.

## Scope

An authority MUST apply identity confinement (§2.18), membership scope
(§2.19) and numeric scope (§2.20) to a `QueryResult` exactly as to an
`Assertion`, and MUST validate every SID in one structurally before
using it — including the SIDs of references inside a `PRIMARY_GROUP`,
`GROUPS` or `MEMBERS` value, not only the `sid` of the result itself.

"Exactly as to an `Assertion`" is meant literally, and it is the
sentence an implementation is most likely to satisfy by halves. An
authority that confines the object a result names, while relaying the
group references beside it unchecked, has left the whole of membership
scope unenforced on this channel — and a source with no permission to
assert a foreign membership can then report one through a name lookup
that it could not report through a logon.

A query is not a weaker channel than a logon. A source that could name a
principal outside its domain here would be able to make `ls -l` display
another source's principals as its own — and, worse, could then be
believed the next time something compared that name to a SID.

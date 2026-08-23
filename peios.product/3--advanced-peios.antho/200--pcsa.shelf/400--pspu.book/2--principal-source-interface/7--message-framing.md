---
title: Message Framing
description: The 20-byte header — the first twelve bytes are PGSS Logon's, unchanged — plus conversation identifiers, size limits and SIDs on the wire.
---

## Header

Every message begins with a 20-byte header:

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `magic` | `PPSI` (`50 50 53 49`) |
| 4 | 2 | `version` | `1` |
| 6 | 2 | `msg_type` | See §2.A |
| 8 | 4 | `total_len` | Header plus body, in bytes |
| 12 | 8 | `conversation` | See below |

The first twelve bytes are PGSS Logon's header, unchanged and at the
same offsets. `total_len` in particular sits where PGSS §2.6 puts it,
which is what lets one transport implementation frame either protocol
off a stream.

## Magic

`PPSI`, checked on every message, fatal to the connection when wrong.

This matters more here than it would for an unrelated protocol, because
PSI and PGSS Logon **share message bodies** (§2.5). A
`CredentialRequest` from one is byte-identical to the other's. Without
distinct magic, a socket plugged into the wrong daemon would decode
several fields correctly before going wrong — which is the failure mode
hardest to diagnose and easiest to miss.

## Conversation identifier

The `conversation` field distinguishes concurrent logons on one
connection.

- **Conversation `0` is reserved** for connection-level messages:
  `Register`, `Registered` and `Changed` (§2.17). It MUST NOT be used
  for a logon or a query.
- Logon and query conversations use identifiers from 1 upward, drawn
  from one space.
- The **authority allocates** them. A source MUST NOT invent one, and
  MUST reply on the identifier it was given.
- An identifier is unique among *live* conversations on one connection.
  An authority MAY reuse one after a conversation has reached a terminal
  state.

A source MUST reject a message on a conversation it does not know, and
MUST NOT treat it as opening a new one. Only `Authenticate` (§2.11),
`Query` (§2.15) and `EnumerateSource` (§2.16) open one, and an authority
MUST NOT open one with an identifier already live.

Rejecting means declining to act on it. A source MUST NOT reply on a
conversation it does not know: an authority MAY have reused the
identifier after a terminal state, so a reply could arrive as a second
terminal message for a conversation that has already ended. Discarding
it, and recording that it happened, is the whole of the obligation.

A source MUST likewise refuse an `Authenticate`, `Query` or
`EnumerateSource` arriving on conversation `0`, which is reserved.

## Size limit

A message MUST NOT exceed **81920 bytes** — larger than PGSS Logon's
ceiling, because a PSI message wraps one.

## Message direction

The high bit of `msg_type` marks a message sent by **the source**. This
follows PGSS Logon's convention that the bit marks the authority for the
matter at hand: on this interface the source is the authority for its
own principals, and the logon authority is the one asking.

## Encoding

PSI shares its codec with PGSS Logon, and PGSS §2.6's encoding rules
apply here unchanged: little-endian multi-byte integers; UTF-8 strings,
length-prefixed and never NUL-terminated; length-framed structures and
array elements, skipped to their declared end; `u32` element counts on
arrays, with stated maxima binding on encoder and decoder alike.

### SIDs on the wire

SIDs are carried as **opaque bytes**, in the binary self-relative form
PCDS specifies, never as text.

They are opaque *to the codec*, which has no business knowing what a SID
is. They are emphatically not opaque to the authority, which MUST
validate every SID it receives before treating it as identity (§2.13).
The obligation to check sits in the process that mints tokens, not in
the layer that moves bytes.

A SID MUST NOT exceed 68 bytes — the eight-byte prelude plus fifteen
sub-authorities, which is the most the encoding's one-byte count admits.

## Body extensibility

The extensibility rules of PGSS §2.6 apply unchanged: fields are
appended only, a new field is optional with a safe default, and a new
enumeration value is a breaking change requiring a version bump. The one
exception is the capability bitmask of §2.8, for the reason given in
§2.B.

One PSI-specific application deserves stating. `Authenticate` (§2.11)
**nests** a whole `LogonStart` inside its own length frame rather than
inlining its fields. The obvious encoding — `LogonStart`'s fields, then
PSI's — is wrong: `LogonStart` belongs to PGSS Logon and grows on PGSS
Logon's schedule, so a field appended there would silently displace the
field after it. Nesting lets the two evolve independently.

The same reasoning applies to every shared body PSI carries, and §2.C
lists them.

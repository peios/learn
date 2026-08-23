---
title: Message Framing
description: The header both channels share — magic, version, message type and size limit — and how a message body may be extended.
---

Both of an authority's channels use the framing specified here without
modification. The identity socket's departures are stated in §2.14; they
concern which message types are served where, not the encoding.

## Header

Every message begins with a 12-byte header:

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `magic` | `PGSL` (`50 47 53 4c`) |
| 4 | 2 | `version` | `1` |
| 6 | 2 | `msg_type` | See §2.A |
| 8 | 4 | `total_len` | Header plus body, in bytes |

`total_len` counts the header. A message is therefore self-delimiting
from its first 12 bytes, and a reader can size its buffer before reading
the body.

## Magic

The magic MUST be checked on every message and MUST cause an immediate,
whole-connection failure when wrong.

This is not decoration. Peios protocols share this codec and this header
layout, and some of them share message bodies. A socket plugged into the
wrong daemon would otherwise *partially* work, which is far worse than
failing outright — a subtle misbehaviour several fields in, rather than
a hard error on byte zero. A protocol reusing this codec MUST take a
distinct magic.

## Version

A peer receiving a `version` it does not implement MUST refuse the
message. An authority MUST refuse with `AccessDenied` carrying
`UnsupportedVersion` where it can still encode one.

## Size limit

A message MUST NOT exceed **65536 bytes** in total. A decoder MUST
reject a header declaring more, without reading the body, and MUST
reject one declaring fewer than the header's own length.

## Message type

The high bit of `msg_type` marks a message sent by the **authority**.
Client messages have it clear. This is a readability property rather
than a security one — a peer MUST validate the message type it received
against what it expected, not merely against the direction bit.

## Encoding

All multi-byte integers are little-endian.

**Strings** are UTF-8 and are **not NUL-terminated**. A string is
encoded as a `u32` byte count followed by exactly that many bytes. A
decoder MUST reject a string whose bytes are not valid UTF-8.

An empty string and an absent optional string are encoded identically,
as a zero byte count. A field documented as optional is therefore absent
when empty, and an implementation MUST NOT distinguish the two.

**Byte strings** are encoded the same way and carry no encoding
requirement.

**Arrays** are encoded as a `u32` element count followed by that many
length-framed structures. Every array in this chapter has a stated
maximum; an encoder MUST refuse to produce a longer one and a decoder
MUST reject one it receives. The same holds for every stated byte limit.

Two distinct length mechanisms therefore appear, and confusing them is
the most likely implementation error:

- **Byte strings and strings** are prefixed with a `u32` byte count, and
  the bytes follow immediately.
- **Structures and array elements** are prefixed with a `u32` byte count
  of the *whole structure*, and a decoder MUST skip to the structure's
  declared end after reading the fields it knows.

The second is what makes the format extensible.

## Body extensibility

The body is a single length-framed structure, and **every structure and
every array element within it is length-framed too**.

A decoder reads the fields it knows and then skips to the structure's
declared end. A field appended by a newer peer is therefore stepped over
rather than mistaken for the next field — which is what makes the format
extensible *inside arrays*, where ignoring trailing bytes at the message
level would not help.

A structure that ends before a field an older encoder never wrote is not
an error. A decoder that reaches the end of a structure's body where an
optional trailing field would have been MUST substitute that field's
documented default (§2.7, §2.9) rather than failing.

The rules this keeps working under are binding on anyone revising this
chapter:

- Fields are **appended only**. Never reordered, never removed, never
  changed in meaning.
- A new field MUST be **optional with a safe default**, because older
  peers will not send it and will not read it.
- Adding a value to an enumeration is a **breaking change** and requires
  a version bump, because every peer is required to understand every
  value it is sent.

The last rule is the one that surprises people. An unknown enumeration
value cannot be safely ignored: a client that skipped an unrecognised
credential type would silently fail to collect something the authority
required, and an authority that skipped an unrecognised logon type would
grant the wrong kind of session.

There are exactly two exceptions, and both are stated where they apply:
`LogonStart.supported_credential_types`, which is a statement of
capability rather than an instruction (§2.7), and the field mask of
`Lookup`, whose reply says which bits it answered (§2.16).

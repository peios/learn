---
title: Message Framing
description: PGSS Logon's header and encoding with PLPS's own magic, and a larger size limit for a whole store's listing.
---

## Header

Every message begins with PGSS Logon's 12-byte header (PGSS §2.6),
unchanged, with this chapter's magic:

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `magic` | `PLPS` (`50 4c 50 53`) |
| 4 | 2 | `version` | `1` |
| 6 | 2 | `msg_type` | See §10.A |
| 8 | 4 | `total_len` | Header plus body, in bytes |

The magic MUST be checked on every message, and MUST end the exchange
when wrong. PLPS shares PGSS Logon's codec and some of its structures,
so a socket plugged into the wrong daemon would otherwise decode several
fields before going wrong.

The high bit of `msg_type` marks a message sent by the **store daemon**,
which is the authority for its own store. A party MUST check the type it
received against the one it expected, not only against that bit.

## Size limit

A message MUST NOT exceed **2 MiB** (2,097,152 bytes) in total, larger
than PGSS Logon's limit so that `Principals` can carry a whole store's
listing (§10.5). A party MUST reject a header declaring more without
reading the body.

## Encoding

Integers, strings, byte strings, arrays and length-framed structures are
encoded exactly as PGSS §2.6 specifies, and a body is one length-framed
structure. The two length mechanisms are the ones that section warns
against confusing: a string or byte string is a `u32` byte count and its
bytes; a structure or array element is a `u32` byte count of the whole
structure, and a decoder skips to that end after the fields it knows.

**Booleans** are a `u8`: zero is false, anything else is true.

**SIDs** are byte strings carrying the binary SID (PCDS §4), at most 68
bytes.

**An optional string** is a `u8` presence flag followed by a string: the
string is meaningful only where the flag is non-zero. It exists where
"leave this alone" and "set this to empty" are both requests a client
makes, and PGSS's empty-means-absent rule could not tell them apart.

**A claim** is encoded as PSI encodes one (§2.13): a length-framed
structure of `name`, `flags`, `value_type` and `values`. Its value types
and flags are PCDS §5.9's, and are closed here as they are on PSI
(§2.A).

## Extending

The rules of PGSS §2.6 bind this chapter: fields are appended only, an
appended field is optional with a stated default, and a new value in an
enumeration is a breaking change requiring a version bump.

A decoder that reaches the end of a structure where an appended field
would have been MUST substitute that field's default. This chapter states
each default where the field is defined; a client and a store daemon of
different ages then degrade rather than fail.

---
title: Data Conventions
description: The data conventions every specification book inherits,
  covering byte order, sizes, layout tables, notation, strings, hashes,
  and timestamps.
---

The conventions in this article hold across every specification book. A
book MUST NOT restate them, and MUST state any point on which it differs.

## Byte order

All multi-byte integer fields are little-endian unless explicitly stated
otherwise.

## Sizes

All sizes and offsets are in bytes. `u8`, `u16`, `u32`, and `u64` denote
unsigned integers of 8, 16, 32, and 64 bits.

## Layout tables

A field layout is given as a table in declaration order. A layout table
is normative: fields appear on the wire in the order listed, with no
padding between them.

## Notation

Hexadecimal values carry the `0x` prefix. Byte sequences are written as
space-separated lowercase hex pairs, `0a 0b 0c`, the form hex dump tools
print. Lowercase here is a deliberate departure from the uppercase
hexadecimal of [Core Style](~psc/core-style) (§1.1).

## Strings

Strings are UTF-8 (RFC 3629). String comparison is byte-for-byte
equality unless stated otherwise.

## Hashes and signatures

Hash values are lowercase hexadecimal unless stated otherwise, matching
the form hashing tools print and files carry, and hash algorithms are
named by their IANA-registered identifiers.

## Timestamps

Timestamps are RFC 3339, in UTC, and end with `Z`.

## What a book's conventions article carries

Because these conventions are shared, a book's conventions article
(§3.1) is short. It MUST carry the book's RFC 2119 declaration, and
SHOULD carry only:

- Notation the book introduces that this article does not list
- Any point on which the book departs from this article
- Pseudocode conventions, if the book uses pseudocode (§2.3)

> [!NOTE]
> A conventions chapter copied into each of four books does not stay
> identical. Duplicated text is where contradictions breed, and the
> contradiction is invisible because nobody reads two copies of the
> same thing side by side.

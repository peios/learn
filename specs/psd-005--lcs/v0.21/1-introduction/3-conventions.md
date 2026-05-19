---
title: Conventions
---

This specification conforms to PSD-001.

## Normative keywords

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in this
specification are to be interpreted as described in RFC 2119.

## Pseudocode

Pseudocode in this specification uses the following conventions,
matching PSD-004 §1.3:

- `|` bitwise OR, `&` bitwise AND, `~` bitwise NOT.
- `|=` and `&=` augmented assignment.
- `->` field access on a pointer/reference.
- `//` single-line comments.
- `→` denotes return type in function signatures.

SID comparison is binary (byte-for-byte equality). Two SIDs match if
and only if every field is identical.

Access mask comparison is bitwise. "Mask A includes right R" means
`(A & R) == R`.

## Ioctl encoding

Ioctl numbers are constructed using the standard Linux `_IOC`
macro: `_IOC(direction, type, number, size)`. The type byte,
direction, and number for each ioctl are listed in §11.1. The
size is the total byte count of the ioctl's argument struct as
defined in §11.2. The final 32-bit
ioctl number is derived from these four components per the Linux
kernel ioctl encoding convention.

## Byte order

All multi-byte integers in LCS data structures, the RSI wire protocol,
and the backup format are little-endian unless explicitly stated
otherwise.

## String encoding

All strings in the LCS interface (key names, value names, hive
names, layer names, paths) are UTF-8 encoded. Case folding for
case-insensitive comparison is applied at the Unicode codepoint
level after decoding from UTF-8, not on raw bytes. The case folding
algorithm is defined in §2.3.

Invalid UTF-8 is rejected with EINVAL before parsing, routing, case
folding, layer resolution, or source dispatch. Null bytes (`\0`)
are rejected in all LCS strings unless a specific field explicitly
permits them.

All configured string length limits are measured in UTF-8 bytes,
not Unicode scalar values or display characters. A string's byte
length excludes any syscall-path terminating null byte.

Syscall paths are copied from userspace as null-terminated C
strings, then validated as UTF-8 bytes excluding the terminator.
Ioctl strings and RSI strings are length-delimited byte sequences;
they do not require a terminator, and a terminator byte included in
the length is a null byte and therefore invalid unless the specific
field explicitly permits it.

## Registry paths

Registry paths use the backslash (`\`) as the canonical separator.
LCS accepts forward slash (`/`) on input and normalises it to
backslash before processing. Paths in this specification always use
the canonical backslash form.

Paths are case-preserving and case-insensitive. The comparison
algorithm is defined in §2.3.

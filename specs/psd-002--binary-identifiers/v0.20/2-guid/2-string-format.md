---
title: String Format
---

## Canonical form

The canonical string representation of a GUID MUST use the following
format:

```
{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
```

The string MUST be exactly 38 characters: an opening brace, 32 hex
digits arranged in 8-4-4-4-12 groups separated by hyphens, and a
closing brace.

The fields map to the string as follows:

| Group | Digits | Source |
|-------|--------|--------|
| 1 | 8 | Data1, most significant nibble first |
| 2 | 4 | Data2, most significant nibble first |
| 3 | 4 | Data3, most significant nibble first |
| 4 | 4 | Data4[0] and Data4[1], in byte order |
| 5 | 12 | Data4[2] through Data4[7], in byte order |

For Data1, Data2, and Data3, the hex representation is of the
numeric value (most significant nibble first), not of the stored
byte order. For Data4, each byte is encoded in sequence with the
high nibble before the low nibble.

> [!INFORMATIVE]
> Example. Given the 16 bytes (in storage order):
>
> ```
> 04 03 02 01  06 05  08 07  09 0a  0b 0c 0d 0e 0f 10
> ```
>
> Data1 = 0x01020304 (little-endian), Data2 = 0x0506, Data3 = 0x0708.
> The string representation is:
>
> ```
> {01020304-0506-0708-090a-0b0c0d0e0f10}
> ```

## Case

Canonical output MUST use lowercase hex digits (`a`–`f`).

## Parsing

Parsers MUST accept both uppercase and lowercase hex digits.

Parsers MUST accept the braced form `{...}` and SHOULD accept the
unbraced form `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.

Parsers MUST reject strings that do not have exactly the right
number of hex digits in each group.

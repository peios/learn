---
title: Binary Format
---

A GUID is a 128-bit (16-byte) value with the following binary layout:

| Offset | Size | Field | Type |
|--------|------|-------|------|
| 0 | 4 | Data1 | uint32, little-endian |
| 4 | 2 | Data2 | uint16, little-endian |
| 6 | 2 | Data3 | uint16, little-endian |
| 8 | 8 | Data4 | uint8[8] |

The total size of a GUID MUST be exactly 16 bytes with no
padding.

Data1, Data2, and Data3 MUST be stored in little-endian byte
order.

Data4 is a raw byte array with no endianness interpretation.

> [!INFORMATIVE]
> This is the mixed-endian layout inherited from DCE RPC and
> MS-DTYP. The first three fields follow the platform's native byte
> order (little-endian on x86), while Data4 is a byte sequence with
> no integer interpretation.

## Nil GUID

The nil GUID is the GUID with all 16 bytes set to zero.

The nil GUID is a valid GUID value. Specifications that require a
non-nil GUID MUST state this requirement explicitly.

The nil GUID MUST NOT be produced by the generation algorithm
defined in §2.4.

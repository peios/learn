---
title: Binary Format
description: The 64-bit LUID — LowPart and HighPart, its boot-scoped uniqueness, and the nil LUID.
---

An LUID (Locally Unique Identifier) is a 64-bit identifier with
boot-scoped local uniqueness, used to identify transient entities
such as logon sessions and privilege instances that do not persist
across reboots. The LUID with all 64 bits set to zero is the
**nil LUID**, a sentinel value meaning "no LUID" or "unset."

An LUID is a 64-bit (8-byte) value with the following binary layout:

| Offset | Size | Field | Type |
|--------|------|-------|------|
| 0 | 4 | LowPart | uint32, little-endian |
| 4 | 4 | HighPart | uint32, little-endian |

The total size of an LUID MUST be exactly 8 bytes with no
padding.

Both fields MUST be stored in little-endian byte order.

> [!NOTE]
> MS-DTYP defines HighPart as a signed 32-bit integer (LONG). Peios
> uses unsigned uint32 for both fields. The signed type in MS-DTYP
> is a Win32 API convention with no semantic purpose — LUID values
> are never negative. See §3.A for the full divergence rationale.

## Nil LUID

The nil LUID is the LUID with all 8 bytes set to zero
(LowPart = 0, HighPart = 0).

The nil LUID is a valid LUID value. The nil LUID MUST NOT be
assigned by the allocation algorithm defined in §3.3.

Specifications that require a non-nil LUID MUST state this
requirement explicitly.

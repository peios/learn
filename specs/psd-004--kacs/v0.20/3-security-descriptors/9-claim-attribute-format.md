---
title: Claim Attribute Format
---

KACS v0.20 uses a Windows-compatible `CLAIM_SECURITY_ATTRIBUTE_RELATIVE_V1`
entry format for:

- resource attributes in `SYSTEM_RESOURCE_ATTRIBUTE_ACE`
- token `user_claims`
- token `device_claims`
- `local_claims` passed to AccessCheck

The claim entry format itself is shared across all four surfaces. When multiple
entries are carried in one buffer (token claims or `local_claims`), KACS wraps
the Windows-compatible entry format in a simple length-prefixed sequence so the
buffer can be parsed deterministically without external metadata.

## Supported types

KACS v0.20 supports these claim value types:

| Type | Value | Notes |
|---|---|---|
| `INT64` | `0x0001` | Signed 64-bit integer. |
| `UINT64` | `0x0002` | Unsigned 64-bit integer. |
| `STRING` | `0x0003` | UTF-16LE string. |
| `SID` | `0x0005` | Binary SID. |
| `BOOLEAN` | `0x0006` | Stored as `u64`; normalized to true/false at resolution time. |
| `OCTET` | `0x0010` | Byte array. |

`FQBN` (`0x0004`) is reserved and not supported in KACS v0.20. Any unsupported
claim type makes the containing claim entry invalid.

## Entry layout

All multibyte integers are little-endian. All offsets are relative to the start
of the claim entry.

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | `NameOffset` | Offset to the UTF-16LE null-terminated attribute name. |
| 4 | 2 | `ValueType` | One of the supported claim value types above. |
| 6 | 2 | `Reserved` | Reserved. Ignored by AccessCheck. Producers SHOULD set to 0. |
| 8 | 4 | `Flags` | Claim flags. |
| 12 | 4 | `ValueCount` | Number of values. May be 0. |
| 16 | `4 * ValueCount` | `ValueOffsets[]` | One relative offset per value. Interpretation depends on `ValueType`. |

Claim flags use the same meanings everywhere this format appears:

| Flag | Value | Meaning |
|---|---|---|
| `CLAIM_SECURITY_ATTRIBUTE_VALUE_CASE_SENSITIVE` | `0x0002` | String/octet comparisons using this attribute are case-sensitive. |
| `CLAIM_SECURITY_ATTRIBUTE_USE_FOR_DENY_ONLY` | `0x0004` | The attribute is visible only to deny-side conditional evaluation. |
| `CLAIM_SECURITY_ATTRIBUTE_DISABLED` | `0x0010` | The attribute is invisible to conditional evaluation. |

Unknown flag bits are preserved but have no defined v0.20 semantics.

## Value encodings

### INT64 / UINT64 / BOOLEAN

For `INT64`, `UINT64`, and `BOOLEAN`, each `ValueOffsets[i]` points directly to
an 8-byte scalar:

- `INT64`: signed 64-bit integer
- `UINT64`: unsigned 64-bit integer
- `BOOLEAN`: unsigned 64-bit integer, normalized at resolution time:
  - `0` = false
  - any non-zero value = true

### STRING

For `STRING`, each `ValueOffsets[i]` points to a 4-byte `u32` named
`StringOffset`. `StringOffset` then points to the actual UTF-16LE
null-terminated string.

Strings are stored without a separate length field. The terminating UTF-16
null (`0x0000`) MUST appear within the containing claim entry.

### SID

For `SID`, each `ValueOffsets[i]` points to a 4-byte `u32` named `SidOffset`.
`SidOffset` then points to a binary SID in the standard SID wire format.

### OCTET

For `OCTET`, each `ValueOffsets[i]` points to a 4-byte `u32` named
`OctetOffset`. `OctetOffset` then points to:

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4 | `Length` | Byte length of the octet string. |
| 4 | `Length` | `Data` | Raw bytes. |

## Single-entry containers

`SYSTEM_RESOURCE_ATTRIBUTE_ACE.ApplicationData` contains exactly one claim
entry and consumes the remainder of the ACE.

## Multi-entry containers

Token claim buffers (`user_claims`, `device_claims`) and `local_claims` use a
KACS claim-array wrapper:

```
repeat until buffer exhausted:
  [entry_len:u32le]
  [entry_bytes: entry_len bytes]
```

Rules:

- `entry_len` MUST be non-zero.
- `entry_len` MUST fit entirely within the containing buffer.
- `entry_bytes` is one complete claim entry using the layout above.
- The parser consumes entries sequentially until the containing buffer length is
  exhausted exactly.

## Validation rules

- The fixed header and `ValueOffsets[]` array MUST fit within the entry.
- Every offset and nested offset MUST remain within the entry bounds.
- Every string name and string value MUST terminate within the entry.
- Every referenced SID MUST be structurally valid.
- A malformed claim entry invalidates the containing surface:
  - malformed resource attribute ACE payload -> malformed SD for AccessCheck
  - malformed token claim buffer -> invalid token spec
  - malformed `local_claims` buffer -> invalid AccessCheck input

`ValueCount = 0` is valid. Empty attributes normalize to absent at resolution
time, as defined in the Conditional ACEs section.

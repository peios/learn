---
title: Token and session specs
type: reference
description: The wire format the caller passes to kacs_create_token to mint a new token, and to kacs_create_session to create a new logon session. This page covers the layout of both, the claim entry format used inside token specs, and the validation rules the kernel applies.
related:
  - peios/wire-formats-reference/overview
  - peios/wire-formats-reference/security-descriptors
  - peios/kernel-abi-reference/syscalls
  - peios/tokens/overview
  - peios/logon-sessions/overview
---

`kacs_create_token` and `kacs_create_session` take wire-format specs that describe what to mint. The specs are self-contained binary records that the kernel parses, validates, and turns into a token or session. This page covers both formats and the supporting claim-entry format used inside token specs.

## Session spec

The session spec is small. It identifies who is signing in and how.

| Bytes | Field | Notes |
|---|---|---|
| 0 | `logon_type` (u8) | Logon type — Interactive (2), Network (3), Batch (4), Service (5), NetworkCleartext (8), NewCredentials (9). |
| 1–2 | `auth_pkg_len` (u16le) | Length of the auth-package string in bytes. |
| 3+ | `auth_pkg` (string) | UTF-8 bytes naming the auth mechanism (e.g. "Kerberos"). Length = `auth_pkg_len`. |
| | `user_sid_len` (u32le) | Length of the user SID in bytes. Appears right after `auth_pkg`. |
| | `user_sid` (binary SID) | The user the session is for. |

Total size: variable. Minimum 15 bytes (smallest auth_pkg + smallest SID). Maximum 4096 bytes total.

Validation:

- `logon_type` must be a recognised value.
- `auth_pkg_len` must be reasonable (within size limit).
- `user_sid` must be well-formed.

The kernel constructs the session, assigns it a fresh `session_id` LUID (the syscall's return value), derives the logon SID `S-1-5-5-{X}-{Y}` from the session ID, and stamps `created_at`.

## Token spec

The token spec is substantially larger. The fixed header is 192 bytes; variable sections follow.

### Fixed header (offsets 0–191)

| Offset | Size | Field | Notes |
|---|---|---|---|
| 0 | 4 | `version` | Must be `TOKEN_SPEC_VERSION` = 2. |
| 4 | 4 | `token_type` | 1 = Primary, 2 = Impersonation. |
| 8 | 4 | `impersonation_level` | 0–3. For Primary tokens, must be 0 (Anonymous). |
| 12 | 4 | `integrity_level` | Integrity RID (0, 4096, 8192, 12288, 16384). |
| 16 | 4 | `mandatory_policy` | Bitmask: `NO_WRITE_UP` (0x01), `NEW_PROCESS_MIN` (0x02). |
| 20 | 4 | _reserved1 (`elevation_type`) | Must be 0. (Elevation set via `KACS_IOC_LINK_TOKENS` post-creation.) |
| 24 | 8 | `auth_id` | Session ID this token belongs to. |
| 32 | 8 | `expiration` | Expiration timestamp; 0 = no expiry. Informational in v0.20. |
| 40 | 8 | `origin` | Originating session LUID for derived tokens. |
| 48 | 4 | `audit_policy` | Bitmask of per-token forced-audit flags. |
| 52 | 4 | `interactive_session_id` | Session number (0 = service, 1+ = interactive). |
| 56 | 4 | `user_sid_off` | Offset (from spec start) to user SID. |
| 60 | 4 | `user_sid_len` | Length of user SID in bytes. |
| 64 | 4 | `groups_off` | Offset to groups list. |
| 68 | 4 | `groups_len` | Length of groups list in bytes. |
| 72 | 4 | `restricted_sids_off` | Offset to restricted SIDs list. |
| 76 | 4 | `restricted_sids_len` | Length. |
| 80 | 4 | `device_groups_off` | Offset. |
| 84 | 4 | `device_groups_len` | Length. |
| 88 | 4 | `restricted_device_groups_off` | Offset. |
| 92 | 4 | `restricted_device_groups_len` | Length. |
| 96 | 4 | `user_claims_off` | Offset to user_claims multi-entry buffer. |
| 100 | 4 | `user_claims_len` | Length. |
| 104 | 4 | `device_claims_off` | Offset. |
| 108 | 4 | `device_claims_len` | Length. |
| 112 | 4 | `default_dacl_off` | Offset to default DACL. |
| 116 | 4 | `default_dacl_len` | Length. |
| 120 | 4 | `owner_sid_index` | Index into groups list (where 0 = user_sid). |
| 124 | 4 | `primary_group_index` | Same. |
| 128 | 4 | `privileges_present` | 64-bit present-bitmask, low 32 bits. |
| 132 | 4 | (continued, high 32 bits) | |
| 136 | 4 | `privileges_enabled` | 64-bit enabled-bitmask, low 32 bits. |
| 140 | 4 | (continued, high 32 bits) | |
| 144 | 4 | `privileges_enabled_by_default` | Low 32. |
| 148 | 4 | (continued) | High 32. |
| 152 | 4 | `confinement_sid_off` | Offset; 0 if not confined. |
| 156 | 4 | `confinement_sid_len` | Length; 0 if not confined. |
| 160 | 4 | `confinement_capabilities_off` | Offset. |
| 164 | 4 | `confinement_capabilities_len` | Length. |
| 168 | 4 | `confinement_exempt` | Boolean (0 or 1). |
| 172 | 4 | `isolation_boundary` | Boolean. Must be 0 unless confinement_sid is set. |
| 176 | 4 | `projected_uid` | Linux UID projection. `65534` if no mapping. |
| 180 | 4 | `projected_gid` | Linux GID projection. |
| 184 | 4 | `supplementary_gids_off` | Offset to supplementary GIDs array (u32 each). |
| 188 | 4 | `supplementary_gids_len` | Length in bytes (4 × number of GIDs). |

Each offset points into the variable section that follows. Length zero with offset zero means "absent". Offsets must point within the spec; the kernel rejects out-of-bounds offsets.

### Variable sections

After the 192-byte header, variable-length data follows. The offsets in the header point to records in this region. Each variable section has its own internal format:

#### Groups list (and the related restricted/device variants)

```
[count:u32le]
[group1: sid_len:u32le, sid bytes, attributes:u32le]
[group2: same]
...
```

Each group entry is `sid_len` (u32) + sid bytes + `attributes` (u32). The attributes are the standard `SE_GROUP_*` flags (MANDATORY 0x01, ENABLED_BY_DEFAULT 0x02, ENABLED 0x04, OWNER 0x08, USE_FOR_DENY_ONLY 0x10, etc.).

#### Restricted SIDs and confinement capabilities

Same format as groups but typically with `attributes = 0` (the kernel ignores attributes on these).

#### User/device claims

Multi-entry claim buffer:

```
[entry1_len:u32le][entry1 bytes]
[entry2_len:u32le][entry2 bytes]
...
```

Until the offset+length region is consumed. Each entry is one claim record.

#### Claim entry format (CLAIM_SECURITY_ATTRIBUTE_RELATIVE_V1)

Each claim entry has a 16-byte header followed by variable data:

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `name_offset` | Offset (from entry start) to the name string. |
| 4 | 2 | `value_type` | INT64 (0x0001), UINT64 (0x0002), STRING (0x0003), SID (0x0005), BOOLEAN (0x0006), OCTET (0x0010). |
| 6 | 2 | `reserved` | Must be 0. |
| 8 | 4 | `flags` | Claim flags: CASE_SENSITIVE (0x0002), USE_FOR_DENY_ONLY (0x0004), DISABLED (0x0010), MANDATORY (0x0020). |
| 12 | 4 | `value_count` | Number of values (single attributes have value_count = 1; multi-valued have more). |
| 16 | 4 × value_count | `value_offsets` | Offsets to each value. |

After the offsets array, the name string (UTF-16LE) and value records follow. Each value's format depends on `value_type`:

| Type | Encoding |
|---|---|
| INT64 | 8 bytes, signed, little-endian. |
| UINT64 | 8 bytes, unsigned, little-endian. |
| STRING | `[length:u32le][UTF-16LE bytes]`. |
| SID | `[length:u32le][binary SID]`. |
| BOOLEAN | 8 bytes; non-zero is TRUE. |
| OCTET | `[length:u32le][bytes]`. |

#### Default DACL

A binary ACL in the standard format covered in [Security descriptors](~peios/wire-formats-reference/security-descriptors). The DACL header plus its ACEs.

#### Supplementary GIDs

An array of u32 little-endian GIDs.

### Validation

The kernel validates the token spec extensively:

- `version` must equal `TOKEN_SPEC_VERSION` (2 in v0.20).
- `token_type` must be 1 or 2.
- For Primary tokens (`token_type = 1`), `impersonation_level` must be 0 (Anonymous).
- `integrity_level` must be one of the defined RIDs.
- `_reserved1` (elevation_type) must be 0.
- `auth_id` must reference an existing session.
- `user_sid` must be well-formed and reasonable.
- `owner_sid_index` and `primary_group_index` must be valid (0 = user_sid, 1+ = group at that index).
- Every offset must point within the spec; every length must fit; no overlapping regions.
- `confinement_sid` and `isolation_boundary`: isolation_boundary cannot be set without confinement_sid.
- Write-restricted tokens (encoded by the way restricted_sids and user_deny_only combine) must satisfy the user_deny_only constraint.
- `ALL_APPLICATION_PACKAGES` (S-1-15-2-1) MUST NOT appear in confinement_capabilities.
- The logon SID MUST NOT be supplied; the kernel injects it from the auth_id.

A failure at any check returns `-EINVAL`. The token is not created.

### What the kernel adds

The kernel sets some fields automatically after validation:

- `token_id`: a fresh LUID.
- `modified_id`: 0 at creation.
- `created_at`: current timestamp.
- `source`: the calling process's identity (typically "authd " or similar).
- The logon SID (derived from `auth_id`) is injected into the groups list with `SE_GROUP_LOGON_ID` set.

After all of this, the kernel returns a token fd with `TOKEN_ALL_ACCESS`.

## Limits

Per-spec maximums:

| Field | Limit |
|---|---|
| Total spec size | 64 KB |
| Number of groups | bounded by spec size (~thousands in practice) |
| Number of privileges | 64 (fits in the bitmask) |
| Number of claim entries | bounded by claim buffer size |

The kernel enforces these at parse time.

## Comparing to runtime token state

A token spec describes what to mint. The minted token's runtime state has the same fields plus a few the kernel adds (token_id, modified_id, created_at, source, the logon SID). The fields the spec sets are the fields visible to `KACS_IOC_QUERY` later — `TokenUser` returns the user SID, `TokenGroups` returns the groups, `TokenPrivileges` returns the privilege bitmasks, etc.

The wire format is the input; the runtime token is the output. Both have the same shape; the wire format is just the serialised version.

## kacs_create_token receives just the spec

The `kacs_create_token` syscall takes a pointer + length to the spec bytes. The spec is self-contained — every offset, every length, every value the kernel needs is in the buffer. There are no other parameters to the syscall beyond `SeCreateTokenPrivilege` (implicit, on the calling token).

This is what makes the token-creation API simple. The caller assembles the spec; the kernel validates and constructs. No multi-step protocol, no out-of-band parameters.

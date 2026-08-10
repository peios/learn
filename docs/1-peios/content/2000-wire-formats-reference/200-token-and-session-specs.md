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
| 0 | `logon_type` (u8) | Logon type — Interactive (2), Network (3), Batch (4), Service (5), NetworkCleartext (8), NewCredentials (9). The full catalogue is in [Other constants](~peios/constants-and-catalogs/other-constants). |
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
| 4 | 1 | `token_type` (u8) | 1 = Primary, 2 = Impersonation. |
| 5 | 1 | `impersonation_level` (u8) | 0–3. For Primary tokens, must be 0 (Anonymous). |
| 6 | 2 | `_reserved0` | Must be 0. |
| 8 | 4 | `integrity_rid` | Integrity RID (0, 4096, 8192, 12288, 16384). |
| 12 | 4 | `mandatory_policy` | Bitmask: `NO_WRITE_UP` (0x01), `NEW_PROCESS_MIN` (0x02). |
| 16 | 8 | `privs_present` | 64-bit bitmask of privileges present on the token. |
| 24 | 8 | `privs_enabled` | 64-bit bitmask of privileges initially enabled (subset of present). The kernel initialises `enabled_by_default` to this same value — there is no separate wire field. |
| 32 | 4 | `_reserved1` | Must be 0. (Elevation type is set only via `KACS_IOC_LINK_TOKENS` post-creation.) |
| 36 | 4 | `projected_uid` | Linux UID projection. `65534` if no mapping. |
| 40 | 4 | `projected_gid` | Linux GID projection. |
| 44 | 4 | `audit_policy` | Bitmask of per-token forced-audit flags. |
| 48 | 8 | `expiration` | Expiration timestamp; 0 = no expiry. Informational in v0.20. |
| 56 | 8 | `session_id` | Logon session ID this token belongs to (used as the token's `auth_id`). |
| 64 | 4 | `owner_sid_index` | 0 = user_sid, 1..N = caller-supplied group at that index. |
| 68 | 4 | `primary_group_index` | Same. |
| 72 | 8 | `source_name` (u8[8]) | Token source name (e.g. `"authd\0\0\0"`). |
| 80 | 8 | `source_id` | Token source identifier (LUID). |
| 88 | 4 | `user_sid_offset` | Offset (from spec start) to the user SID. |
| 92 | 4 | `groups_offset` | Offset to the groups array. |
| 96 | 4 | `groups_count` | Number of group entries. |
| 100 | 4 | `default_dacl_offset` | Offset to the default DACL. 0 = none. |
| 104 | 4 | `default_dacl_len` | Length. 0 = none. |
| 108 | 4 | `user_claims_offset` | Offset to the user_claims multi-entry buffer. |
| 112 | 4 | `user_claims_len` | Total byte length. |
| 116 | 4 | `device_claims_offset` | Offset. |
| 120 | 4 | `device_claims_len` | Length. |
| 124 | 4 | `device_groups_offset` | Offset. |
| 128 | 4 | `device_groups_count` | Entry count. |
| 132 | 4 | `restricted_sids_offset` | Offset. |
| 136 | 4 | `restricted_sids_count` | Entry count. |
| 140 | 4 | `confinement_sid_offset` | Offset; 0 if not confined. |
| 144 | 4 | `confinement_sid_len` | Length; 0 if not confined. |
| 148 | 4 | `confinement_caps_offset` | Offset. |
| 152 | 4 | `confinement_caps_count` | Entry count. |
| 156 | 1 | `confinement_exempt` (u8) | 1 = exempt from confinement. |
| 157 | 1 | `write_restricted` (u8) | 1 = write-restricted mode. |
| 158 | 1 | `user_deny_only` (u8) | 1 = user SID matches deny ACEs only. |
| 159 | 1 | `isolation_boundary` (u8) | 1 = enable namespace filtering (not enforced in v0.20). Must be 0 unless confinement_sid is set. |
| 160 | 4 | `supp_gids_offset` | Offset to the projected supplementary GIDs array (u32le each). |
| 164 | 4 | `supp_gids_count` | Entry count. |
| 168 | 4 | `restricted_device_groups_offset` | Offset. |
| 172 | 4 | `restricted_device_groups_count` | Entry count. |
| 176 | 8 | `origin` | Originating logon-session LUID for derived tokens; 0 for non-derived. |
| 184 | 4 | `interactive_session_id` | Session number (0 = service, 1+ = interactive). |
| 188 | 4 | `lcs_credentials_offset` | Offset to the optional LCS registry-credentials extension. 0 = none. |

Each offset points into the variable section that follows. An offset/length (or offset/count) pair that is both zero means the section is absent. Offsets must point within the spec; the kernel rejects out-of-bounds offsets. Sections may appear in any order.

### Variable sections

After the 192-byte header, variable-length data follows. The offsets in the header point to records in this region. Each variable section has its own internal format:

#### Groups array (and the restricted/device variants)

```
[group1: sid_len:u32le, sid bytes, attributes:u32le]
[group2: same]
...
```

The entry count comes from the corresponding `_count` header field — there is no inline count. Each entry is `sid_len` (u32) + sid bytes + `attributes` (u32). The attributes are the standard `SE_GROUP_*` flags — the full flag catalogue is in [Well-known SIDs](~peios/constants-and-catalogs/well-known-sids).

#### Restricted SIDs and confinement capabilities

Same per-entry format as groups but typically with `attributes = 0` (the kernel ignores attributes on these).

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
| 0 | 4 | `name_offset` | Offset (from entry start) to the UTF-16LE null-terminated name string. |
| 4 | 2 | `value_type` | Claim value type. The value catalogue is in [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags). |
| 6 | 2 | `reserved` | Ignored by AccessCheck; producers should set 0. |
| 8 | 4 | `flags` | Claim flags. The flag catalogue is in [ACE types and flags](~peios/constants-and-catalogs/ace-types-and-flags). |
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

An array of u32 little-endian GIDs, `supp_gids_count` entries.

#### LCS registry credentials (optional)

At `lcs_credentials_offset`. A 16-byte header — `version` (u32, must be 1), `_reserved` (u32, must be 0), `scope_count` (u32, max 256), `private_layer_count` (u32, max 256) — followed by `scope_count` raw 16-byte GUIDs, then `private_layer_count` u32le name byte-lengths, then the concatenated UTF-8 private layer names. Scope GUIDs must be non-nil and unique; layer names must be 1–255 bytes, must not contain `\`, `/`, or NUL, and must be unique under case-insensitive matching. The section is consumed exactly; trailing bytes are malformed.

### Validation

The kernel validates the token spec extensively:

- `version` must equal `TOKEN_SPEC_VERSION` (2 in v0.20).
- `token_type` must be 1 or 2.
- For Primary tokens (`token_type = 1`), `impersonation_level` must be 0 (Anonymous).
- `integrity_rid` must be one of the defined RIDs.
- All reserved fields must be 0. In particular `_reserved1` must be 0 — the kernel always creates tokens with elevation type Default.
- `session_id` must reference an existing logon session.
- All SIDs must be structurally well-formed.
- `owner_sid_index` and `primary_group_index` must be valid (0 = user_sid, 1..N = caller-supplied group at that index). The owner must be the user SID or a group with `SE_GROUP_OWNER`.
- Every offset must point within the spec; every length must fit.
- If `isolation_boundary` is set, `confinement_sid` must be present.
- If `write_restricted` is set, `user_deny_only` must also be set.
- The caller-supplied group count plus the kernel-injected logon SID must fit the 1024-entry group limit.
- The LCS registry-credentials extension, when present, must satisfy the structural rules above (version, counts, uniqueness, name constraints).
- The logon SID must not be supplied in the groups array; the kernel injects it from the session ID.

Note the kernel never synthesizes `ALL_APPLICATION_PACKAGES` (S-1-15-2-1): a normally-confined token carries it in `confinement_capabilities` because the caller put it there, and strict confinement omits it — see [Confinement](~peios/confinement/overview).

A failure at any check returns `-EINVAL`. The token is not created.

### What the kernel adds

The kernel sets some fields automatically after validation:

- `token_id`: a fresh LUID.
- `token_guid`: a fresh UUIDv4.
- `modified_id`: initialised to the new `token_id`.
- `created_at`: current timestamp.
- `elevation_type`: always Default. (`source` is caller-supplied — the `source_name`/`source_id` header fields.)
- The logon SID (derived from `session_id` as `S-1-5-5-{high}-{low}`) is appended to the groups array with `SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED | SE_GROUP_LOGON_ID`.

After all of this, the kernel returns a token fd with `TOKEN_ALL_ACCESS`.

## Limits

The kernel enforces the per-spec maximums at parse time: total spec size 64 KB (minimum 192 bytes — the bare header), at most 1024 groups including the injected logon SID, 64 privileges (the bitmask width), and claim entries bounded by the claim buffer size. The full cross-format limits catalogue is in [Other constants](~peios/constants-and-catalogs/other-constants).

## Comparing to runtime token state

A token spec describes what to mint. The minted token's runtime state has the same fields plus a few the kernel adds (token_id, token_guid, modified_id, created_at, the logon SID). The fields the spec sets are the fields visible to `KACS_IOC_QUERY` later — `TokenUser` returns the user SID, `TokenGroups` returns the groups, `TokenPrivileges` returns the privilege bitmasks, etc.

The wire format is the input; the runtime token is the output. Both have the same shape; the wire format is just the serialised version.

## kacs_create_token receives just the spec

The `kacs_create_token` syscall takes a pointer + length to the spec bytes. The spec is self-contained — every offset, every length, every value the kernel needs is in the buffer. There are no other parameters to the syscall beyond `SeCreateTokenPrivilege` (implicit, on the calling token).

This is what makes the token-creation API simple. The caller assembles the spec; the kernel validates and constructs. No multi-step protocol, no out-of-band parameters.

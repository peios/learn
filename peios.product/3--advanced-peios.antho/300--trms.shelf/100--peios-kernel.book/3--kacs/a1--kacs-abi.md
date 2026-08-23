---
title: KACS ABI Reference
description: Every KACS syscall number, structure layout, constant and enumeration, generated from the uapi headers and measured by compilation.
---

Every name, value, offset and size in this appendix is generated
from `pkm/uapi/pkm/` by `pkm/tools/gen-kacs-abi.py`, with struct
layouts measured by compiling a probe against the real headers.
Regenerate it whenever the ABI changes; do not edit it by hand.

The names here are the ones a program actually compiles against.

## Syscall numbers

Signatures are read from the `SYSCALL_DEFINE` sites in `pkm/kacs/`.

| Number | Constant | Signature |
|---:|---|---|
| 1000 | `SYS_KACS_OPEN_SELF_TOKEN` | `kacs_open_self_token(unsigned int flags, u32 access_mask)` |
| 1001 | `SYS_KACS_OPEN_PROCESS_TOKEN` | `kacs_open_process_token(int pidfd, u32 access_mask)` |
| 1002 | `SYS_KACS_OPEN_THREAD_TOKEN` | `kacs_open_thread_token(int pidfd, int tid, u32 access_mask)` |
| 1003 | `SYS_KACS_CREATE_TOKEN` | `kacs_create_token(const void __user *spec, size_t spec_len)` |
| 1004 | `SYS_KACS_CREATE_LOGON_SESSION` | `kacs_create_logon_session(const void __user *spec, size_t spec_len)` |
| 1005 | `SYS_KACS_SET_PSB` | `kacs_set_psb(int pidfd, u32 mitigations)` |
| 1006 | `SYS_KACS_DESTROY_EMPTY_LOGON_SESSION` | `kacs_destroy_empty_logon_session(u64 auth_id)` |
| 1010 | `SYS_KACS_OPEN_PEER_TOKEN` | `kacs_open_peer_token(int sock_fd)` |
| 1011 | `SYS_KACS_IMPERSONATE_PEER` | `kacs_impersonate_peer(int sock_fd)` |
| 1012 | `SYS_KACS_REVERT` | `kacs_revert(void)` |
| 1013 | `SYS_KACS_SET_IMPERSONATION_LEVEL` | `kacs_set_impersonation_level(int sock_fd, u32 level)` |
| 1020 | `SYS_KACS_OPEN` | `kacs_open(int dirfd, const char __user *path, struct kacs_open_how __user *uhow, size_t howsize, u32 __user *status_out)` |
| 1021 | `SYS_KACS_GET_SD` | `kacs_get_sd(int dirfd, const char __user *path, u32 security_info, void __user *buf, u32 buf_len, u32 flags)` |
| 1022 | `SYS_KACS_SET_SD` | `kacs_set_sd(int dirfd, const char __user *path, u32 security_info, const void __user *sd_buf, u32 sd_len, u32 flags)` |
| 1023 | `SYS_KACS_ACCESS_CHECK` | `kacs_access_check(const void __user *uargs)` |
| 1024 | `SYS_KACS_ACCESS_CHECK_LIST` | `kacs_access_check_list(const void __user *uargs, struct kacs_node_result __user *results, u32 results_count)` |
| 1025 | `SYS_KACS_SET_CAAP` | `kacs_set_caap(const void __user *policy_sid, u32 policy_sid_len, const void __user *spec, u32 spec_len)` |
| 1026 | `SYS_KACS_GET_MOUNT_POLICY` | `kacs_get_mount_policy(int fd, struct kacs_mount_policy_args __user *uargs, size_t argsize)` |
| 1027 | `SYS_KACS_SET_MOUNT_POLICY` | `kacs_set_mount_policy(int fd, struct kacs_mount_policy_args __user *uargs, size_t argsize)` |

`uapi/pkm/syscall.h` also registers the KMES and LCS numbers,
1090–1102, documented in their own chapters.

## Structure layouts

### `struct kacs_query_args`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `token_class` |
| 4 | 4 | `__u32` | `buf_len` |
| 8 | 8 | `__u64` | `buf_ptr` |

### `struct kacs_adjust_privs_args`

Total size 24 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `count` |
| 4 | 4 | `__u32` | `_pad` |
| 8 | 8 | `__u64` | `data_ptr` |
| 16 | 8 | `__u64` | `previous_enabled` |

### `struct kacs_priv_entry`

Total size 8 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `luid` |
| 4 | 4 | `__u32` | `attributes` |

### `struct kacs_adjust_groups_args`

Total size 144 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `count` |
| 4 | 4 | `__u32` | `_pad` |
| 8 | 8 | `__u64` | `data_ptr` |
| 16 | 128 | `__u64``[16]` | `previous_state` |

### `struct kacs_duplicate_args`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `access_mask` |
| 4 | 4 | `__u32` | `token_type` |
| 8 | 4 | `__u32` | `impersonation_level` |
| 12 | 4 | `__s32` | `result_fd` |

### `struct kacs_group_entry`

Total size 8 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `index` |
| 4 | 4 | `__u32` | `enable` |

### `struct kacs_adjust_default_args`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 8 | `__u64` | `dacl_ptr` |
| 8 | 4 | `__u32` | `dacl_len` |
| 12 | 2 | `__u16` | `owner_index` |
| 14 | 2 | `__u16` | `group_index` |

### `struct kacs_restrict_args`

Total size 40 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 8 | `__u64` | `privs_to_delete` |
| 8 | 4 | `__u32` | `num_deny_indices` |
| 12 | 4 | `__u32` | `num_restrict_sids` |
| 16 | 4 | `__u32` | `data_len` |
| 20 | 4 | `__u32` | `flags` |
| 24 | 8 | `__u64` | `data_ptr` |
| 32 | 4 | `__s32` | `result_fd` |
| 36 | 4 | `__u32` | `_pad` |

### `struct kacs_link_tokens_args`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__s32` | `elevated_fd` |
| 4 | 4 | `__s32` | `filtered_fd` |
| 8 | 8 | `__u64` | `logon_session_id` |

### `struct kacs_get_linked_token_args`

Total size 4 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__s32` | `result_fd` |

### `struct kacs_access_check_args`

Total size 136 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `caller_size` |
| 4 | 4 | `__s32` | `token_fd` |
| 8 | 8 | `__u64` | `sd_ptr` |
| 16 | 4 | `__u32` | `sd_len` |
| 20 | 4 | `__u32` | `desired_access` |
| 24 | 4 | `__u32` | `mapping_read` |
| 28 | 4 | `__u32` | `mapping_write` |
| 32 | 4 | `__u32` | `mapping_execute` |
| 36 | 4 | `__u32` | `mapping_all` |
| 40 | 8 | `__u64` | `self_sid_ptr` |
| 48 | 4 | `__u32` | `self_sid_len` |
| 52 | 4 | `__u32` | `privilege_intent` |
| 56 | 8 | `__u64` | `object_tree_ptr` |
| 64 | 4 | `__u32` | `object_tree_count` |
| 68 | 4 | `__u32` | `_pad0` |
| 72 | 8 | `__u64` | `local_claims_ptr` |
| 80 | 4 | `__u32` | `local_claims_len` |
| 84 | 4 | `__u32` | `_pad1` |
| 88 | 8 | `__u64` | `granted_out_ptr` |
| 96 | 4 | `__u32` | `pip_type` |
| 100 | 4 | `__u32` | `pip_trust` |
| 104 | 8 | `__u64` | `audit_context_ptr` |
| 112 | 4 | `__u32` | `audit_context_len` |
| 116 | 4 | `__u32` | `_pad2` |
| 120 | 8 | `__u64` | `continuous_audit_out_ptr` |
| 128 | 8 | `__u64` | `staging_mismatch_out_ptr` |

### `struct kacs_object_type_entry`

Total size 20 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 2 | `__u16` | `level` |
| 2 | 2 | `__u16` | `_reserved` |
| 4 | 16 | `__u8``[16]` | `guid` |

### `struct kacs_node_result`

Total size 8 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `granted` |
| 4 | 4 | `__s32` | `status` |

### `struct kacs_open_how`

Total size 32 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `desired_access` |
| 4 | 4 | `__u32` | `create_disposition` |
| 8 | 4 | `__u32` | `create_options` |
| 12 | 4 | `__u32` | `flags` |
| 16 | 8 | `__u64` | `sd_ptr` |
| 24 | 4 | `__u32` | `sd_len` |
| 28 | 4 | `__u32` | `__pad` |

### `struct kacs_mount_policy_args`

Total size 32 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `policy` |
| 4 | 4 | `__u32` | `flags` |
| 8 | 4 | `__u32` | `generation` |
| 12 | 4 | `__u32` | `__pad0` |
| 16 | 8 | `__u64` | `template_sd_ptr` |
| 24 | 4 | `__u32` | `template_sd_len` |
| 28 | 4 | `__u32` | `__pad1` |

### `struct kacs_generic_mapping`

Total size 16 bytes.

| Offset | Size | Type | Field |
|---:|---:|---|---|
| 0 | 4 | `__u32` | `read` |
| 4 | 4 | `__u32` | `write` |
| 8 | 4 | `__u32` | `execute` |
| 12 | 4 | `__u32` | `all` |

## Token constants

From `uapi/pkm/token.h`.

*kacs_open_self_token (SYS_KACS_OPEN_SELF_TOKEN) flags.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_OPEN_REAL` | `0x01` (1) |

*Per-handle token rights (the low 16 bits of a token access mask).*

| Constant | Value |
|---|---|
| `KACS_TOKEN_ASSIGN_PRIMARY` | `0x0001` (1) |
| `KACS_TOKEN_DUPLICATE` | `0x0002` (2) |
| `KACS_TOKEN_IMPERSONATE` | `0x0004` (4) |
| `KACS_TOKEN_QUERY` | `0x0008` (8) |
| `KACS_TOKEN_QUERY_SOURCE` | `0x0010` (16) |
| `KACS_TOKEN_ADJUST_PRIVS` | `0x0020` (32) |
| `KACS_TOKEN_ADJUST_GROUPS` | `0x0040` (64) |
| `KACS_TOKEN_ADJUST_DEFAULT` | `0x0080` (128) |
| `KACS_TOKEN_ADJUST_INTERACTIVITY_SCOPE` | `0x0100` (256) |
| `KACS_TOKEN_ALL_ACCESS` | `0x000F01FF` |

*Token ioctl interface identifier.*

| Constant | Value |
|---|---|
| `KACS_IOC_MAGIC` | `0x4B` (75) |

*kacs_priv_entry.attributes bits.*

| Constant | Value |
|---|---|
| `KACS_PRIVILEGE_ATTR_ENABLED` | `0x00000002` (2) |
| `KACS_PRIVILEGE_ATTR_REMOVED` | `0x00000004` (4) |

*kacs_adjust_privs bulk-reset flag (not a per-entry attribute).*

| Constant | Value |
|---|---|
| `KACS_PRIVILEGE_RESET_ALL_DEFAULTS` | `0x80000000` |

*kacs_restrict_args.flags bits.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_RESTRICT_WRITE_RESTRICTED` | `0x00000001` (1) |

*Token type (KACS_TOKEN_CLASS_TYPE).*

| Constant | Value |
|---|---|
| `KACS_TOKEN_TYPE_PRIMARY` | `0x01` (1) |
| `KACS_TOKEN_TYPE_IMPERSONATION` | `0x02` (2) |

*Impersonation level (KACS_TOKEN_CLASS_IMPERSONATION_LEVEL).*

| Constant | Value |
|---|---|
| `KACS_IMLEVEL_ANONYMOUS` | `0x00` (0) |
| `KACS_IMLEVEL_IDENTIFICATION` | `0x01` (1) |
| `KACS_IMLEVEL_IMPERSONATION` | `0x02` (2) |
| `KACS_IMLEVEL_DELEGATION` | `0x03` (3) |

*Elevation type (KACS_TOKEN_CLASS_ELEVATION_TYPE).*

| Constant | Value |
|---|---|
| `KACS_ELEVATION_DEFAULT` | `0x01` (1) |
| `KACS_ELEVATION_FULL` | `0x02` (2) |
| `KACS_ELEVATION_LIMITED` | `0x03` (3) |

*Mandatory-policy bits (KACS_TOKEN_CLASS_MANDATORY_POLICY).*

| Constant | Value |
|---|---|
| `KACS_TOKEN_MANDATORY_POLICY_NO_WRITE_UP` | `0x00000001` (1) |
| `KACS_TOKEN_MANDATORY_POLICY_NEW_PROCESS_MIN` | `0x00000002` (2) |

Per-token audit-policy bits — the create-token spec `audit_policy` field
(KACS_TOKEN_SPEC_OFF_AUDIT_POLICY). They select which access-check
outcomes the token's object accesses generate audit events for.

| Constant | Value |
|---|---|
| `KACS_AUDIT_POLICY_OBJECT_ACCESS_SUCCESS` | `0x00000001` (1) |
| `KACS_AUDIT_POLICY_OBJECT_ACCESS_FAILURE` | `0x00000002` (2) |
| `KACS_AUDIT_POLICY_PRIVILEGE_USE_SUCCESS` | `0x00000004` (4) |
| `KACS_AUDIT_POLICY_PRIVILEGE_USE_FAILURE` | `0x00000008` (8) |

*Logon type (KACS_TOKEN_CLASS_LOGON_TYPE).*

| Constant | Value |
|---|---|
| `KACS_LOGON_TYPE_INTERACTIVE` | `2` |
| `KACS_LOGON_TYPE_NETWORK` | `3` |
| `KACS_LOGON_TYPE_BATCH` | `4` |
| `KACS_LOGON_TYPE_SERVICE` | `5` |
| `KACS_LOGON_TYPE_NETWORK_CLEARTEXT` | `8` |
| `KACS_LOGON_TYPE_NEW_CREDENTIALS` | `9` |

*Maximum number of groups a token may carry.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_MAX_GROUPS` | `1024` |

*Number of 64-bit words in a group enabled-state bitmask (KACS_TOKEN_MAX_GROUPS / 64).*

| Constant | Value |
|---|---|
| `KACS_TOKEN_GROUP_MASK_WORDS` | `16` |

*kacs_create_token (SYS_KACS_CREATE_TOKEN) spec wire format.*

The (spec, len) buffer the syscall consumes is a fixed
KACS_TOKEN_SPEC_HEADER_BYTES-byte header followed by variable-length
sections at header-specified byte offsets. An offset/length (or
offset/count) pair that is both zero means the section is absent.
Sections may appear in any order; every offset+length is validated to
fall within the buffer. The header is not a C struct (it carries packed
mixed-width fields and crosses the syscall boundary as raw bytes); read
each field at its KACS_TOKEN_SPEC_OFF_* offset. Its fields, in order:
__u32 version must be KACS_TOKEN_SPEC_VERSION __u8 token_type
KACS_TOKEN_TYPE_ __u8 impersonation_level KACS_IMLEVEL_ __u8
_reserved0[2] must be 0 __u32 integrity_rid integrity-level RID __u32
mandatory_policy KACS_TOKEN_MANDATORY_POLICY_* bits __u64 privs_present
privilege bitmask (KACS_SE_*_PRIVILEGE) __u64 privs_enabled initially
enabled privileges (subset) __u32 _reserved1 must be 0 (elevation set
only by LINK_TOKENS) __u32 projected_uid Linux UID for credential
projection __u32 projected_gid Linux GID for credential projection __u32
audit_policy per-token audit flags __u64 expiration expiry timestamp (0
= none) __u64 logon_session_id logon session ID (auth_id) __u32
owner_sid_index 0 = user SID, 1..N = caller group __u32
primary_group_index 0 = user SID, 1..N = caller group __u8
source_name[8] token source name __u64 source_id token source LUID __u32
user_sid_offset byte offset to the user SID __u32 groups_offset byte
offset to the groups array __u32 groups_count number of group entries
__u32 default_dacl_offset byte offset to the default DACL (0 = none)
__u32 default_dacl_len default DACL byte length (0 = none) __u32
user_claims_offset byte offset to user claims (0 = none) __u32
user_claims_len user claims byte length (0 = none) __u32
device_claims_offset byte offset to device claims (0 = none) __u32
device_claims_len device claims byte length (0 = none) __u32
device_groups_offset byte offset to device groups (0 = none) __u32
device_groups_count number of device-group entries (0 = none) __u32
restricted_sids_offset byte offset to restricted SIDs (0 = none) __u32
restricted_sids_count number of restricted-SID entries (0 = none) __u32
confinement_sid_offset byte offset to confinement SID (0 = none) __u32
confinement_sid_len confinement SID byte length (0 = none) __u32
confinement_caps_offset byte offset to confinement caps (0 = none) __u32
confinement_caps_count number of confinement-cap entries (0 = none) __u8
confinement_exempt 1 = exempt from confinement __u8 write_restricted 1 =
write-restricted mode __u8 user_deny_only 1 = user SID matches deny ACEs
only __u8 isolation_boundary 1 = enable namespace filtering __u32
supp_gids_offset byte offset to supplementary GIDs (0 = none) __u32
supp_gids_count number of supplementary-GID entries (0 = none) __u32
restricted_device_groups_offset byte offset (0 = none) __u32
restricted_device_groups_count entry count (0 = none) __u64 origin
originating logon-session LUID (0 = none) __u32 interactivity_scope
interactive session number __u32 lcs_credentials_offset byte offset to
the LCS extension (0 = none) A group/device-group/restricted-
SID/confinement-cap/restricted-device-group entry is [__u32
sid_len][__u8 sid[sid_len]][__u32 attributes]. A supplementary-GIDs
section is supp_gids_count little-endian __u32 GIDs. All multi-byte
header and section scalars are little-endian.

| Constant | Value |
|---|---|
| `KACS_TOKEN_SPEC_VERSION` | `2` |
| `KACS_TOKEN_SPEC_HEADER_BYTES` | `192` |
| `KACS_TOKEN_SPEC_MIN_BYTES` | `192` |
| `KACS_TOKEN_SPEC_MAX_BYTES` | `65536` |

*Byte offsets of the fixed token-spec header fields.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_SPEC_OFF_VERSION` | `0` |
| `KACS_TOKEN_SPEC_OFF_TOKEN_TYPE` | `4` |
| `KACS_TOKEN_SPEC_OFF_IMPERSONATION_LEVEL` | `5` |
| `KACS_TOKEN_SPEC_OFF_RESERVED0` | `6` |
| `KACS_TOKEN_SPEC_OFF_INTEGRITY_RID` | `8` |
| `KACS_TOKEN_SPEC_OFF_MANDATORY_POLICY` | `12` |
| `KACS_TOKEN_SPEC_OFF_PRIVS_PRESENT` | `16` |
| `KACS_TOKEN_SPEC_OFF_PRIVS_ENABLED` | `24` |
| `KACS_TOKEN_SPEC_OFF_RESERVED1` | `32` |
| `KACS_TOKEN_SPEC_OFF_PROJECTED_UID` | `36` |
| `KACS_TOKEN_SPEC_OFF_PROJECTED_GID` | `40` |
| `KACS_TOKEN_SPEC_OFF_AUDIT_POLICY` | `44` |
| `KACS_TOKEN_SPEC_OFF_EXPIRATION` | `48` |
| `KACS_TOKEN_SPEC_OFF_LOGON_SESSION_ID` | `56` |
| `KACS_TOKEN_SPEC_OFF_OWNER_SID_INDEX` | `64` |
| `KACS_TOKEN_SPEC_OFF_PRIMARY_GROUP_INDEX` | `68` |
| `KACS_TOKEN_SPEC_OFF_SOURCE_NAME` | `72` |
| `KACS_TOKEN_SPEC_OFF_SOURCE_ID` | `80` |
| `KACS_TOKEN_SPEC_OFF_USER_SID_OFFSET` | `88` |
| `KACS_TOKEN_SPEC_OFF_GROUPS_OFFSET` | `92` |
| `KACS_TOKEN_SPEC_OFF_GROUPS_COUNT` | `96` |
| `KACS_TOKEN_SPEC_OFF_DEFAULT_DACL_OFFSET` | `100` |
| `KACS_TOKEN_SPEC_OFF_DEFAULT_DACL_LEN` | `104` |
| `KACS_TOKEN_SPEC_OFF_USER_CLAIMS_OFFSET` | `108` |
| `KACS_TOKEN_SPEC_OFF_USER_CLAIMS_LEN` | `112` |
| `KACS_TOKEN_SPEC_OFF_DEVICE_CLAIMS_OFFSET` | `116` |
| `KACS_TOKEN_SPEC_OFF_DEVICE_CLAIMS_LEN` | `120` |
| `KACS_TOKEN_SPEC_OFF_DEVICE_GROUPS_OFFSET` | `124` |
| `KACS_TOKEN_SPEC_OFF_DEVICE_GROUPS_COUNT` | `128` |
| `KACS_TOKEN_SPEC_OFF_RESTRICTED_SIDS_OFFSET` | `132` |
| `KACS_TOKEN_SPEC_OFF_RESTRICTED_SIDS_COUNT` | `136` |
| `KACS_TOKEN_SPEC_OFF_CONFINEMENT_SID_OFFSET` | `140` |
| `KACS_TOKEN_SPEC_OFF_CONFINEMENT_SID_LEN` | `144` |
| `KACS_TOKEN_SPEC_OFF_CONFINEMENT_CAPS_OFFSET` | `148` |
| `KACS_TOKEN_SPEC_OFF_CONFINEMENT_CAPS_COUNT` | `152` |
| `KACS_TOKEN_SPEC_OFF_CONFINEMENT_EXEMPT` | `156` |
| `KACS_TOKEN_SPEC_OFF_WRITE_RESTRICTED` | `157` |
| `KACS_TOKEN_SPEC_OFF_USER_DENY_ONLY` | `158` |
| `KACS_TOKEN_SPEC_OFF_ISOLATION_BOUNDARY` | `159` |
| `KACS_TOKEN_SPEC_OFF_SUPP_GIDS_OFFSET` | `160` |
| `KACS_TOKEN_SPEC_OFF_SUPP_GIDS_COUNT` | `164` |
| `KACS_TOKEN_SPEC_OFF_RESTRICTED_DEVICE_GROUPS_OFFSET` | `168` |
| `KACS_TOKEN_SPEC_OFF_RESTRICTED_DEVICE_GROUPS_COUNT` | `172` |
| `KACS_TOKEN_SPEC_OFF_ORIGIN` | `176` |
| `KACS_TOKEN_SPEC_OFF_INTERACTIVITY_SCOPE` | `184` |
| `KACS_TOKEN_SPEC_OFF_LCS_CREDENTIALS_OFFSET` | `188` |

*Byte length of the fixed token-source-name field.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_SPEC_SOURCE_NAME_BYTES` | `8` |

Optional LCS registry-credentials extension, located at the token-spec
header's lcs_credentials_offset. The section is a fixed
KACS_TOKEN_LCS_EXT_HEADER_BYTES-byte header bounded by the next active
variable-section offset or the end of the spec; it is consumed exactly
(trailing bytes are malformed). Header fields, in order: __u32 version
must be KACS_TOKEN_LCS_EXT_VERSION __u32 _reserved must be 0 __u32
scope_count private hive scope GUIDs (<= max) __u32 private_layer_count
private layer names (<= max) Payload: scope_count raw 16-byte GUIDs,
then private_layer_count little-endian __u32 name byte lengths, then the
concatenated UTF-8 layer names. Scope GUIDs must be non-nil and unique;
layer names must be 1.. KACS_TOKEN_LCS_MAX_LAYER_NAME_BYTES bytes, must
not contain '\\', '/', or NUL, and must be unique under case-insensitive
matching.

| Constant | Value |
|---|---|
| `KACS_TOKEN_LCS_EXT_VERSION` | `1` |
| `KACS_TOKEN_LCS_EXT_HEADER_BYTES` | `16` |
| `KACS_TOKEN_LCS_SCOPE_GUID_BYTES` | `16` |
| `KACS_TOKEN_LCS_MAX_SCOPE_GUIDS` | `256` |
| `KACS_TOKEN_LCS_MAX_PRIVATE_LAYERS` | `256` |
| `KACS_TOKEN_LCS_MAX_LAYER_NAME_BYTES` | `255` |

*Byte offsets of the fixed LCS-extension header fields.*

| Constant | Value |
|---|---|
| `KACS_TOKEN_LCS_EXT_OFF_VERSION` | `0` |
| `KACS_TOKEN_LCS_EXT_OFF_RESERVED` | `4` |
| `KACS_TOKEN_LCS_EXT_OFF_SCOPE_COUNT` | `8` |
| `KACS_TOKEN_LCS_EXT_OFF_PRIVATE_LAYER_COUNT` | `12` |

*kacs_create_logon_session (SYS_KACS_CREATE_LOGON_SESSION) spec wire format.*

The (spec, len) buffer the syscall consumes is, in order: __u8
logon_type one of KACS_LOGON_TYPE_* above __le16 auth_pkg_len byte
length of the auth-package name __u8 auth_pkg[auth_pkg_len] auth-package
name (valid UTF-8) __le32 user_sid_len byte length of the user SID __u8
user_sid[user_sid_len] binary SID of the authenticated user The buffer
is consumed exactly: 7 + auth_pkg_len + user_sid_len must equal len. The
kernel assigns the session ID and derives the logon SID from it.

| Constant | Value |
|---|---|
| `KACS_LOGON_SESSION_SPEC_MIN_BYTES` | `15` |
| `KACS_LOGON_SESSION_SPEC_MAX_BYTES` | `4096` |

*Byte offsets of the fixed-position session-spec fields.*

| Constant | Value |
|---|---|
| `KACS_LOGON_SESSION_SPEC_OFF_LOGON_TYPE` | `0` |
| `KACS_LOGON_SESSION_SPEC_OFF_AUTH_PKG_LEN` | `1` |
| `KACS_LOGON_SESSION_SPEC_OFF_AUTH_PKG` | `3` |

*Token-handle ioctls.*

| Constant | Value |
|---|---|
| `KACS_IOC_QUERY` | `0xC0104B00` |
| `KACS_IOC_ADJUST_PRIVS` | `0x40184B01` |
| `KACS_IOC_DUPLICATE` | `0xC0104B02` |
| `KACS_IOC_INSTALL` | `0x00004B03` |
| `KACS_IOC_RESTRICT` | `0xC0284B04` |
| `KACS_IOC_LINK_TOKENS` | `0x40104B05` |
| `KACS_IOC_GET_LINKED_TOKEN` | `0xC0044B06` |
| `KACS_IOC_ADJUST_GROUPS` | `0x40904B07` |
| `KACS_IOC_IMPERSONATE` | `0x00004B08` |
| `KACS_IOC_ADJUST_DEFAULT` | `0x40104B09` |
| `KACS_IOC_ADJUST_INTERACTIVITY_SCOPE` | `0x40044B0A` |

*Token information classes (kacs_query_args.token_class).*

| Constant | Value |
|---|---|
| `KACS_TOKEN_CLASS_USER` | `0x01` (1) |
| `KACS_TOKEN_CLASS_GROUPS` | `0x02` (2) |
| `KACS_TOKEN_CLASS_PRIVILEGES` | `0x03` (3) |
| `KACS_TOKEN_CLASS_TYPE` | `0x04` (4) |
| `KACS_TOKEN_CLASS_INTEGRITY_LEVEL` | `0x05` (5) |
| `KACS_TOKEN_CLASS_OWNER` | `0x06` (6) |
| `KACS_TOKEN_CLASS_PRIMARY_GROUP` | `0x07` (7) |
| `KACS_TOKEN_CLASS_INTERACTIVITY_SCOPE` | `0x08` (8) |
| `KACS_TOKEN_CLASS_RESTRICTED_SIDS` | `0x09` (9) |
| `KACS_TOKEN_CLASS_SOURCE` | `0x0A` (10) |
| `KACS_TOKEN_CLASS_STATISTICS` | `0x0B` (11) |
| `KACS_TOKEN_CLASS_ORIGIN` | `0x0C` (12) |
| `KACS_TOKEN_CLASS_ELEVATION_TYPE` | `0x0D` (13) |
| `KACS_TOKEN_CLASS_DEVICE_GROUPS` | `0x0E` (14) |
| `KACS_TOKEN_CLASS_APPCONTAINER_SID` | `0x0F` (15) |
| `KACS_TOKEN_CLASS_CAPABILITIES` | `0x10` (16) |
| `KACS_TOKEN_CLASS_MANDATORY_POLICY` | `0x11` (17) |
| `KACS_TOKEN_CLASS_LOGON_TYPE` | `0x12` (18) |
| `KACS_TOKEN_CLASS_LOGON_SID` | `0x13` (19) |
| `KACS_TOKEN_CLASS_DEFAULT_DACL` | `0x14` (20) |
| `KACS_TOKEN_CLASS_IMPERSONATION_LEVEL` | `0x15` (21) |
| `KACS_TOKEN_CLASS_USER_CLAIMS` | `0x16` (22) |
| `KACS_TOKEN_CLASS_DEVICE_CLAIMS` | `0x17` (23) |
| `KACS_TOKEN_CLASS_PROJECTED_SUPPLEMENTARY_GIDS` | `0x18` (24) |

Privileges, as single-bit masks within a token's 64-bit privilege word
(present / enabled / enabled-by-default / used are each one such word).
Named for the Windows privilege identifiers (SeTcbPrivilege, …).

| Constant | Value |
|---|---|
| `KACS_SE_CREATE_TOKEN_PRIVILEGE` | `4` |
| `KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` | `8` |
| `KACS_SE_LOCK_MEMORY_PRIVILEGE` | `16` |
| `KACS_SE_INCREASE_QUOTA_PRIVILEGE` | `32` |
| `KACS_SE_TCB_PRIVILEGE` | `128` |
| `KACS_SE_SECURITY_PRIVILEGE` | `256` |
| `KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` | `512` |
| `KACS_SE_LOAD_DRIVER_PRIVILEGE` | `1024` |
| `KACS_SE_SYSTEM_PROFILE_PRIVILEGE` | `2048` |
| `KACS_SE_SYSTEMTIME_PRIVILEGE` | `4096` |
| `KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` | `8192` |
| `KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` | `16384` |
| `KACS_SE_BACKUP_PRIVILEGE` | `131072` |
| `KACS_SE_RESTORE_PRIVILEGE` | `262144` |
| `KACS_SE_SHUTDOWN_PRIVILEGE` | `524288` |
| `KACS_SE_DEBUG_PRIVILEGE` | `0x100000` (1048576) |
| `KACS_SE_AUDIT_PRIVILEGE` | `0x200000` (2097152) |
| `KACS_SE_CHANGE_NOTIFY_PRIVILEGE` | `0x800000` (8388608) |
| `KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` | `0x1000000` (16777216) |
| `KACS_SE_IMPERSONATE_PRIVILEGE` | `0x20000000` (536870912) |
| `KACS_SE_RELABEL_PRIVILEGE` | `0x100000000` (4294967296) |
| `KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE` | `0x800000000` (34359738368) |
| `KACS_SE_BIND_PRIVILEGED_PORT_PRIVILEGE` | `0x8000000000000000` (9223372036854775808) |

## AccessCheck constants

From `uapi/pkm/access.h`.

*Full size of kacs_access_check_args the current kernel copies.*

| Constant | Value |
|---|---|
| `KACS_ACCESS_CHECK_ARGS_SIZE` | `136` |

*Minimum caller_size the kernel accepts (the v1 / v0.20 layout).*

| Constant | Value |
|---|---|
| `KACS_ACCESS_CHECK_ARGS_V1_SIZE` | `40` |

*Byte size of one kacs_object_type_entry in the object-type tree array.*

| Constant | Value |
|---|---|
| `KACS_OBJECT_TYPE_ENTRY_SIZE` | `20` |

*Largest object-audit-context buffer the kernel accepts.*

| Constant | Value |
|---|---|
| `KACS_ACCESS_CHECK_MAX_AUDIT_CONTEXT_LEN` | `4096` |

*Largest @Local claims blob the kernel accepts (local_claims_ptr).*

| Constant | Value |
|---|---|
| `KACS_ACCESS_CHECK_MAX_LOCAL_CLAIMS_LEN` | `65536` |

*Largest object-type tree entry count the kernel accepts.*

| Constant | Value |
|---|---|
| `KACS_ACCESS_CHECK_MAX_OBJECT_TYPE_COUNT` | `1024` |

Claim value types — the discriminant of one attribute in the @Local
claims array (local_claims_ptr).

| Constant | Value |
|---|---|
| `KACS_CLAIM_TYPE_INT64` | `0x0001` (1) |
| `KACS_CLAIM_TYPE_UINT64` | `0x0002` (2) |
| `KACS_CLAIM_TYPE_STRING` | `0x0003` (3) |
| `KACS_CLAIM_TYPE_SID` | `0x0005` (5) |
| `KACS_CLAIM_TYPE_BOOLEAN` | `0x0006` (6) |
| `KACS_CLAIM_TYPE_OCTET` | `0x0010` (16) |

*Claim attribute flags.*

| Constant | Value |
|---|---|
| `KACS_CLAIM_ATTR_CASE_SENSITIVE` | `0x0002` (2) |
| `KACS_CLAIM_ATTR_USE_FOR_DENY_ONLY` | `0x0004` (4) |
| `KACS_CLAIM_ATTR_DISABLED` | `0x0010` (16) |

Central Access Policy (CAAP) spec wire format — the (spec, spec_len)
buffer kacs_set_caap (SYS_KACS_SET_CAAP) consumes. A non-empty spec
replaces the policy identified by the call's policy SID; a NULL/zero
spec removes it. The buffer is a fixed prefix followed by rule_count
per-rule sections, and is consumed exactly (trailing bytes are
rejected). It is not a C struct (the rule sections are variable-length);
read it as raw bytes: __u8 version must be KACS_CAAP_SPEC_VERSION __le32
rule_count number of rules that follow (<= max) rule_count * { __le32
applies_to_len [__u8 applies_to[applies_to_len]] conditional-expression
bytecode; 0 = always __le32 effective_dacl_len [__u8
effective_dacl[...]] binary ACL; length MUST be nonzero __le32
effective_sacl_len [__u8 effective_sacl[...]] (0 = none) __le32
staged_dacl_len [__u8 staged_dacl[...]] (0 = none) __le32
staged_sacl_len [__u8 staged_sacl[...]] (0 = none) } Every length-
prefixed field uses a little-endian __u32 length and is bounded by
KACS_CAAP_MAX_FIELD_BYTES; ACL payloads additionally parse under the
security-descriptor size limit (KACS_CAAP_MAX_ACL_BYTES). ACLs use the
binary ACL format from <pkm/sd.h>; applies_to is conditional-ACE
bytecode.

| Constant | Value |
|---|---|
| `KACS_CAAP_SPEC_VERSION` | `0x01` (1) |
| `KACS_CAAP_MAX_SPEC_BYTES` | `262144` |
| `KACS_CAAP_MAX_RULE_COUNT` | `256` |
| `KACS_CAAP_MAX_FIELD_BYTES` | `65536` |
| `KACS_CAAP_MAX_ACL_BYTES` | `65535` |

*Byte offsets of the fixed CAAP-spec prefix fields.*

| Constant | Value |
|---|---|
| `KACS_CAAP_SPEC_OFF_VERSION` | `0` |
| `KACS_CAAP_SPEC_OFF_RULE_COUNT` | `1` |

*Byte length of the fixed CAAP-spec prefix (version + rule_count).*

| Constant | Value |
|---|---|
| `KACS_CAAP_SPEC_PREFIX_BYTES` | `5` |

## File and open constants

From `uapi/pkm/file.h`.

*Minimum caller-supplied size accepted for each argument block.*

| Constant | Value |
|---|---|
| `KACS_OPEN_HOW_MIN_SIZE` | `16` |
| `KACS_MOUNT_POLICY_ARGS_MIN_SIZE` | `16` |

*Create dispositions (kacs_open_how.create_disposition).*

| Constant | Value |
|---|---|
| `KACS_DISPOSITION_SUPERSEDE` | `0` |
| `KACS_DISPOSITION_OPEN` | `1` |
| `KACS_DISPOSITION_CREATE` | `2` |
| `KACS_DISPOSITION_OPEN_IF` | `3` |
| `KACS_DISPOSITION_OVERWRITE` | `4` |
| `KACS_DISPOSITION_OVERWRITE_IF` | `5` |

*Create options (kacs_open_how.create_options).*

| Constant | Value |
|---|---|
| `KACS_CREATE_OPT_DIRECTORY` | `0x0001` (1) |
| `KACS_CREATE_OPT_DELETE_ON_CLOSE` | `0x0002` (2) |

*kacs_open_how.flags bits.*

| Constant | Value |
|---|---|
| `KACS_BACKUP_INTENT` | `0x00000001` (1) |
| `KACS_RESTORE_INTENT` | `0x00000002` (2) |

*File and directory object-specific access rights (the low 16 bits of a file access mask).*

The directory aliases name the same bit as the file right it acts as for
a directory object.

| Constant | Value |
|---|---|
| `KACS_FILE_READ_DATA` | `0x00000001` (1) |
| `KACS_FILE_WRITE_DATA` | `0x00000002` (2) |
| `KACS_FILE_APPEND_DATA` | `0x00000004` (4) |
| `KACS_FILE_READ_EA` | `0x00000008` (8) |
| `KACS_FILE_WRITE_EA` | `0x00000010` (16) |
| `KACS_FILE_EXECUTE` | `0x00000020` (32) |
| `KACS_FILE_DELETE_CHILD` | `0x00000040` (64) |
| `KACS_FILE_READ_ATTRIBUTES` | `0x00000080` (128) |
| `KACS_FILE_WRITE_ATTRIBUTES` | `0x00000100` (256) |
| `KACS_FILE_LIST_DIRECTORY` | `1` |
| `KACS_FILE_TRAVERSE` | `32` |
| `KACS_FILE_ADD_FILE` | `2` |
| `KACS_FILE_ADD_SUBDIRECTORY` | `4` |

*Mount-policy values (kacs_mount_policy_args.policy).*

| Constant | Value |
|---|---|
| `KACS_MOUNT_POLICY_UNMANAGED` | `1` |
| `KACS_MOUNT_POLICY_DENY_MISSING` | `2` |
| `KACS_MOUNT_POLICY_SYNTHESIZE_EPHEMERAL` | `3` |
| `KACS_MOUNT_POLICY_SYNTHESIZE_PERSISTENT` | `4` |

*Status word kacs_open writes back, describing what happened to the file.*

| Constant | Value |
|---|---|
| `KACS_STATUS_OPENED` | `1` |
| `KACS_STATUS_CREATED` | `2` |
| `KACS_STATUS_OVERWRITTEN` | `3` |
| `KACS_STATUS_SUPERSEDED` | `4` |

## Process access rights

From `uapi/pkm/process.h`.

*KACS process object-specific access rights (the low 16 bits of a process access mask).*

Named for the Windows process rights; an access check folds the generic
bits (<pkm/sd.h>) into these via the process generic mapping.

| Constant | Value |
|---|---|
| `KACS_PROCESS_TERMINATE` | `0x00000001` (1) |
| `KACS_PROCESS_SIGNAL` | `0x00000002` (2) |
| `KACS_PROCESS_VM_READ` | `0x00000010` (16) |
| `KACS_PROCESS_VM_WRITE` | `0x00000020` (32) |
| `KACS_PROCESS_DUP_HANDLE` | `0x00000040` (64) |
| `KACS_PROCESS_SET_INFORMATION` | `0x00000200` (512) |
| `KACS_PROCESS_QUERY_INFORMATION` | `0x00000400` (1024) |
| `KACS_PROCESS_SUSPEND_RESUME` | `0x00000800` (2048) |
| `KACS_PROCESS_QUERY_LIMITED` | `0x00001000` (4096) |

## Process mitigation bits

From `uapi/pkm/psb.h`.

*Process Security Block (PSB) process-mitigation bits.*

The `mitigations` argument of kacs_set_psb (SYS_KACS_SET_PSB) is a
bitmask of these flags. Setting a bit is activation-backed: KACS either
places the target process in the protected state (or verifies it already
satisfies the invariant) before committing, and rejects later operations
that would disable the protection. Each mitigation is enforced at its
own enforcement point and persists across exec. Only the bits in
KACS_MIT_ALL are valid; any other bit set in the request is rejected.
KACS_MIT_CFI is a legacy alias: requesting it sets both KACS_MIT_CFIF
and KACS_MIT_CFIB, and the alias bit itself is not retained.

| Constant | Value | Notes |
|---|---|---|
| `KACS_MIT_WXP` | `0x001` (1) | Write-XOR-Execute protection |
| `KACS_MIT_TLP` | `0x002` (2) | Trusted Library Paths |
| `KACS_MIT_LSV` | `0x004` (4) | Library Signature Verification |
| `KACS_MIT_CFI` | `0x008` (8) | legacy alias: CFIF \| CFIB |
| `KACS_MIT_UI_ACCESS` | `0x010` (16) | UI interaction (reserved) |
| `KACS_MIT_NO_CHILD` | `0x020` (32) | cannot fork (one-way) |
| `KACS_MIT_CFIF` | `0x040` (64) | forward-edge CFI (Intel IBT) |
| `KACS_MIT_CFIB` | `0x080` (128) | backward-edge CFI (shadow stack) |
| `KACS_MIT_PIE` | `0x100` (256) | reject non-PIE binaries at exec |
| `KACS_MIT_SML` | `0x200` (512) | speculation mitigation lock |

*All valid mitigation bits OR'd together — the accepted-request mask.*

| Constant | Value |
|---|---|
| `KACS_MIT_ALL` | `0x3FF` (1023) |

## Security descriptor constants

From `uapi/pkm/sd.h`.

*Byte length of the self-relative security-descriptor header.*

| Constant | Value |
|---|---|
| `KACS_SD_HEADER_BYTES` | `20` |

SECURITY_INFORMATION selector bits — which components of a security
descriptor a kacs_get_sd / kacs_set_sd call reads or writes.

| Constant | Value |
|---|---|
| `KACS_SECINFO_OWNER` | `0x00000001` (1) |
| `KACS_SECINFO_GROUP` | `0x00000002` (2) |
| `KACS_SECINFO_DACL` | `0x00000004` (4) |
| `KACS_SECINFO_SACL` | `0x00000008` (8) |
| `KACS_SECINFO_LABEL` | `0x00000010` (16) |

*SECURITY_DESCRIPTOR_CONTROL bits — the SD header `control` field.*

| Constant | Value |
|---|---|
| `KACS_SD_OWNER_DEFAULTED` | `0x0001` (1) |
| `KACS_SD_GROUP_DEFAULTED` | `0x0002` (2) |
| `KACS_SD_DACL_PRESENT` | `0x0004` (4) |
| `KACS_SD_DACL_DEFAULTED` | `0x0008` (8) |
| `KACS_SD_SACL_PRESENT` | `0x0010` (16) |
| `KACS_SD_SACL_DEFAULTED` | `0x0020` (32) |
| `KACS_SD_DACL_TRUSTED` | `0x0040` (64) |
| `KACS_SD_SERVER_SECURITY` | `0x0080` (128) |
| `KACS_SD_DACL_AUTO_INHERIT_REQ` | `0x0100` (256) |
| `KACS_SD_SACL_AUTO_INHERIT_REQ` | `0x0200` (512) |
| `KACS_SD_DACL_AUTO_INHERITED` | `0x0400` (1024) |
| `KACS_SD_SACL_AUTO_INHERITED` | `0x0800` (2048) |
| `KACS_SD_DACL_PROTECTED` | `0x1000` (4096) |
| `KACS_SD_SACL_PROTECTED` | `0x2000` (8192) |
| `KACS_SD_RM_CONTROL_VALID` | `0x4000` (16384) |
| `KACS_SD_SELF_RELATIVE` | `0x8000` (32768) |

*Access-mask bits — standard rights (bits 16-24) and generic rights (bits 28-31).*

The low 16 bits of a mask are object-class specific; see <pkm/file.h>
and <pkm/token.h> for those.

| Constant | Value |
|---|---|
| `KACS_ACCESS_DELETE` | `0x00010000` (65536) |
| `KACS_ACCESS_READ_CONTROL` | `0x00020000` |
| `KACS_ACCESS_WRITE_DAC` | `0x00040000` |
| `KACS_ACCESS_WRITE_OWNER` | `0x00080000` |
| `KACS_ACCESS_SYNCHRONIZE` | `0x00100000` |
| `KACS_ACCESS_ACCESS_SYSTEM_SECURITY` | `0x01000000` |
| `KACS_ACCESS_MAXIMUM_ALLOWED` | `0x02000000` |
| `KACS_ACCESS_GENERIC_ALL` | `0x10000000` |
| `KACS_ACCESS_GENERIC_EXECUTE` | `0x20000000` |
| `KACS_ACCESS_GENERIC_WRITE` | `0x40000000` |
| `KACS_ACCESS_GENERIC_READ` | `0x80000000` |

*ACE types — the `ace_type` byte of an ACE header (MS-DTYP 2.4.4.1).*

| Constant | Value |
|---|---|
| `KACS_ACE_TYPE_ACCESS_ALLOWED` | `0x00` (0) |
| `KACS_ACE_TYPE_ACCESS_DENIED` | `0x01` (1) |
| `KACS_ACE_TYPE_SYSTEM_AUDIT` | `0x02` (2) |
| `KACS_ACE_TYPE_SYSTEM_ALARM` | `0x03` (3) |
| `KACS_ACE_TYPE_ACCESS_ALLOWED_COMPOUND` | `0x04` (4) |
| `KACS_ACE_TYPE_ACCESS_ALLOWED_OBJECT` | `0x05` (5) |
| `KACS_ACE_TYPE_ACCESS_DENIED_OBJECT` | `0x06` (6) |
| `KACS_ACE_TYPE_SYSTEM_AUDIT_OBJECT` | `0x07` (7) |
| `KACS_ACE_TYPE_SYSTEM_ALARM_OBJECT` | `0x08` (8) |
| `KACS_ACE_TYPE_ACCESS_ALLOWED_CALLBACK` | `0x09` (9) |
| `KACS_ACE_TYPE_ACCESS_DENIED_CALLBACK` | `0x0A` (10) |
| `KACS_ACE_TYPE_ACCESS_ALLOWED_CALLBACK_OBJECT` | `0x0B` (11) |
| `KACS_ACE_TYPE_ACCESS_DENIED_CALLBACK_OBJECT` | `0x0C` (12) |
| `KACS_ACE_TYPE_SYSTEM_AUDIT_CALLBACK` | `0x0D` (13) |
| `KACS_ACE_TYPE_SYSTEM_ALARM_CALLBACK` | `0x0E` (14) |
| `KACS_ACE_TYPE_SYSTEM_AUDIT_CALLBACK_OBJECT` | `0x0F` (15) |
| `KACS_ACE_TYPE_SYSTEM_ALARM_CALLBACK_OBJECT` | `0x10` (16) |
| `KACS_ACE_TYPE_SYSTEM_MANDATORY_LABEL` | `0x11` (17) |
| `KACS_ACE_TYPE_SYSTEM_RESOURCE_ATTRIBUTE` | `0x12` (18) |
| `KACS_ACE_TYPE_SYSTEM_SCOPED_POLICY_ID` | `0x13` (19) |
| `KACS_ACE_TYPE_SYSTEM_PROCESS_TRUST_LABEL` | `0x14` (20) |
| `KACS_ACE_TYPE_SYSTEM_ACCESS_FILTER` | `0x15` (21) |

Two of these have a constant and nothing behind it. The ACE parser in
`kacs-core` dispatches on 0x00–0x03, 0x05–0x14 and classifies every
other value as opaque, so an ACE of type 0x04 or 0x15 is skipped during
evaluation and written back byte-for-byte on serialisation. The
constants exist so that a decoder can put a name to the byte. libpeios'
SDDL codec does, printing 0x15 as `SYSTEM_ACCESS_FILTER`; the `sd`
utility does not, and renders both as `OTHER(0x04)` and `OTHER(0x15)`.
PCDS §5.4 records the same state normatively.

*ACE header `ace_flags` byte — inheritance and audit control.*

| Constant | Value |
|---|---|
| `KACS_ACE_FLAG_OBJECT_INHERIT` | `0x01` (1) |
| `KACS_ACE_FLAG_CONTAINER_INHERIT` | `0x02` (2) |
| `KACS_ACE_FLAG_NO_PROPAGATE_INHERIT` | `0x04` (4) |
| `KACS_ACE_FLAG_INHERIT_ONLY` | `0x08` (8) |
| `KACS_ACE_FLAG_INHERITED` | `0x10` (16) |
| `KACS_ACE_FLAG_SUCCESSFUL_ACCESS` | `0x40` (64) |
| `KACS_ACE_FLAG_FAILED_ACCESS` | `0x80` (128) |

Mandatory-label policy bits — the __le32 access mask of a
KACS_ACE_TYPE_SYSTEM_MANDATORY_LABEL ACE. They control which DACL-
granted rights a caller whose integrity level does not dominate the
object's label (the "up" direction) is denied. Each bit suppresses the
rights mapped from the corresponding generic class; unknown bits MUST be
ignored.

| Constant | Value |
|---|---|
| `KACS_SYSTEM_MANDATORY_LABEL_NO_READ_UP` | `0x00000001` (1) |
| `KACS_SYSTEM_MANDATORY_LABEL_NO_WRITE_UP` | `0x00000002` (2) |
| `KACS_SYSTEM_MANDATORY_LABEL_NO_EXECUTE_UP` | `0x00000004` (4) |

Object-ACE body `Flags` field — the __le32 at object-ACE body offset 8,
distinct from the 1-byte `ace_flags` header field above. Indicates which
optional GUIDs the object-ACE body carries.

| Constant | Value |
|---|---|
| `KACS_ACE_OBJECT_TYPE_PRESENT` | `0x00000001` (1) |
| `KACS_ACE_INHERITED_OBJECT_TYPE_PRESENT` | `0x00000002` (2) |

## SID constants

From `uapi/pkm/sid.h`.

*Largest sub_authority_count a valid SID may declare.*

| Constant | Value |
|---|---|
| `KACS_SID_MAX_SUB_AUTHORITIES` | `15` |

*Encoded byte length of a SID with the given sub-authority count.*

| Constant | Value |
|---|---|
| `KACS_SID_BYTE_LEN(count)` | `(8 + 4 * (count))` |

*SID_AND_ATTRIBUTES "Attributes" bits (MS-DTYP 2.4.4).*

These describe how a group or restricted SID participates in an access
check. MS-DTYP names them for groups; they apply to any
SID_AND_ATTRIBUTES entry.

| Constant | Value |
|---|---|
| `KACS_SID_GROUP_MANDATORY` | `0x00000001` (1) |
| `KACS_SID_GROUP_ENABLED_BY_DEFAULT` | `0x00000002` (2) |
| `KACS_SID_GROUP_ENABLED` | `0x00000004` (4) |
| `KACS_SID_GROUP_OWNER` | `0x00000008` (8) |
| `KACS_SID_GROUP_USE_FOR_DENY_ONLY` | `0x00000010` (16) |
| `KACS_SID_GROUP_INTEGRITY` | `0x00000020` (32) |
| `KACS_SID_GROUP_INTEGRITY_ENABLED` | `0x00000040` (64) |
| `KACS_SID_GROUP_RESOURCE` | `0x20000000` |
| `KACS_SID_GROUP_LOGON_ID` | `0xC0000000` |

## Token query payloads

The class numbers above come from the header; these are the payloads
each one returns. Sizes are in bytes; a variable-length payload uses
the shapes below. An invalid class returns `EINVAL`.

Two repeating shapes appear throughout. A **SID array** is
`[count:u32le]` followed by `count` entries of
`[sid_len:u32le][sid_bytes][attributes:u32le]`, and reports a count of
zero when the array is empty rather than an empty payload. A **claims
array** is `[count:u32le]` followed by `count` entries of
`[entry_len:u32le][entry_bytes]`. A bare SID is the SID bytes alone,
and an absent optional SID or ACL is zero bytes.

| Class | Payload |
|---|---|
| `USER` | Bare SID. |
| `GROUPS` | SID array. |
| `PRIVILEGES` | 32 bytes: present, enabled, enabled-by-default and used, four `u64` in that order. |
| `TYPE` | `u32`, 4 bytes. |
| `INTEGRITY_LEVEL` | The mandatory-label SID `S-1-16-<level>`, 12 bytes. |
| `OWNER` | Bare SID, resolved through the owner index: 0 is the user SID, N is `groups[N-1]`. |
| `PRIMARY_GROUP` | Bare SID, resolved the same way. |
| `INTERACTIVITY_SCOPE` | `u32`, 4 bytes. |
| `RESTRICTED_SIDS` | SID array; count 0 on an unrestricted token. |
| `SOURCE` | 16 bytes: an 8-byte name followed by a `u64` LUID. |
| `STATISTICS` | 40 bytes: token id, LogonSession id, modified id, token type, a reserved zero, and expiration. |
| `ORIGIN` | `u64`, 8 bytes. |
| `ELEVATION_TYPE` | `u32`, 4 bytes. |
| `DEVICE_GROUPS` | SID array. |
| `APPCONTAINER_SID` | Bare SID; empty when the token is unconfined. |
| `CAPABILITIES` | SID array. |
| `MANDATORY_POLICY` | `u32`, 4 bytes. |
| `LOGON_TYPE` | `u32`, 4 bytes, read from the LogonSession. |
| `LOGON_SID` | Bare SID, derived from the LogonSession id. |
| `DEFAULT_DACL` | Binary ACL; empty when none is set. |
| `IMPERSONATION_LEVEL` | `u32`, 4 bytes. |
| `USER_CLAIMS` | Claims array. |
| `DEVICE_CLAIMS` | Claims array. |
| `PROJECTED_SUPPLEMENTARY_GIDS` | `[count:u32le]` followed by `count` `u32` GIDs. |

Nine token fields have no query class at all: `created_at`,
`token_guid`, `audit_policy`, `write_restricted`, `user_deny_only`,
`isolation_boundary`, `confinement_exempt`, the projected UID and GID
— only the supplementary GIDs are reportable —
`restricted_device_groups`, and the LCS registry credentials.

## Names that differ from the specifications

This manual uses the names `uapi/pkm/` declares, and the generated
tables above are authoritative for them. A reader may instead arrive
holding the name PCDS uses, which is MS-DTYP's — a legitimate spelling,
not an obsolete one, and the one a third party implementing PCDS will
have. This table maps those onto the headers.

| PCDS / MS-DTYP | uapi name |
|---|---|
| `ACCESS_ALLOWED_ACE_TYPE`, `SYSTEM_AUDIT_ACE_TYPE`, ... | `KACS_ACE_TYPE_ACCESS_ALLOWED`, `KACS_ACE_TYPE_SYSTEM_AUDIT`, ... (the qualifier moves to the front) |
| `KACS_REAL_TOKEN` | `KACS_TOKEN_OPEN_REAL` |
| `KACS_LEVEL_*` | `KACS_IMLEVEL_*` |
| `KACS_FILE_SUPERSEDE`, `_OPEN`, ... | `KACS_DISPOSITION_*` |
| `OWNER_SECURITY_INFORMATION`, ... | `KACS_SECINFO_*` |
| `SE_PRIVILEGE_ENABLED` / `_REMOVED` | `KACS_PRIVILEGE_ATTR_ENABLED` / `_REMOVED` |
| `KACS_PRIV_RESET_ALL_DEFAULTS` | `KACS_PRIVILEGE_RESET_ALL_DEFAULTS` |
| `KACS_RESTRICT_WRITE_RESTRICTED` | `KACS_TOKEN_RESTRICT_WRITE_RESTRICTED` |
| `SE_GROUP_*` | `KACS_SID_GROUP_*` |
| `TOKEN_CLASS_*` | `KACS_TOKEN_CLASS_*` |

The PIP tiers have no public names at all. The Protected type (512)
and the `PeiosTcb` trust level (8192) exist only as kernel-private
constants, and nothing in `uapi/pkm/` defines None, Protected or
Isolated. A program reasoning about tiers compares the numbers
(§3.7).

## What is not here

Required rights, error codes and validation rules are properties of
the implementation rather than of the headers, so they are documented
with the operations themselves: token rights and the per-ioctl
requirements in §3.2.8, the file rights in §3.9, the process rights
in §3.3.3, and the privileges in §3.4.2.

Two neighbouring ABIs are generated or documented separately.
`uapi/pkm/trace.h` is a versioned, append-only ABI of tracepoint
reason, operation and state codes intended for tooling.
`uapi/pkm/kmes.h` and `uapi/pkm/lcs.h` belong to their own chapters.

## Build configuration

`CONFIG_SECURITY_PKM=y` and `CONFIG_RUST=y` are required, as are
`CONFIG_STRICT_DEVMEM=y` and `CONFIG_MODULE_SIG_FORCE=y` -- the last
two enforced at initialisation rather than only at build (§3.7).
`CONFIG_SECURITY_SELINUX`, `_APPARMOR`, `_SMACK` and `_TOMOYO` are
refused by Kconfig dependency; `CONFIG_BPF_LSM` is refused only at
runtime, so a kernel enabling both configures and builds and then
fails to initialise. `CONFIG_LSM` is never parsed.

Two further symbols gate large bodies of code:
`CONFIG_SECURITY_PKM_KUNIT`, which compiles in the test harness and,
in the signing path, a different and publicly known verification key
(§3.6); and `CONFIG_STRATAFS_FS`, without which the copy-up API of
§3.9.7 is inert.

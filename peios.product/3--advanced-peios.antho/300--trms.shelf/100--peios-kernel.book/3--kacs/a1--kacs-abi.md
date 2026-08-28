---
title: KACS ABI Reference
description: Every KACS syscall number, structure layout, constant and enumeration, generated from the uapi headers and measured by compilation.
---

Every name, value, offset and size in this appendix is generated
from `pkm/uapi/pkm/` by `pkm/tools/gen-kacs-abi.py`, with struct
layouts measured by compiling a probe against the real headers.
Regenerate it whenever the ABI changes; do not edit it by hand.

The names here are the ones a program actually compiles against.
Everything about the ABI a compiler cannot measure -- token query
payload shapes, the specification spellings that differ from these
names, what is documented elsewhere, and the kernel configuration
-- is in the notes appendix, §3.D, which this generator does not
touch.

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
| 1012 | `SYS_KACS_REVERT` | `kacs_revert(void)` |
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
| `KACS_SE_MANAGE_VOLUME_PRIVILEGE` | `0x10000000` (268435456) |
| `KACS_SE_IMPERSONATE_PRIVILEGE` | `0x20000000` (536870912) |
| `KACS_SE_RELABEL_PRIVILEGE` | `0x100000000` (4294967296) |
| `KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE` | `0x800000000` (34359738368) |
| `KACS_SE_BIND_PRIVILEGED_PORT_PRIVILEGE` | `0x8000000000000000` (9223372036854775808) |

## socket.h

From `uapi/pkm/socket.h`.

*KACS socket options — peer identity on local sockets.*

KACS captures a connecting client's identity onto the accepted end of an
AF_UNIX SOCK_STREAM / SOCK_SEQPACKET connection at connect(). This
header is the setsockopt(2)/getsockopt(2) surface through which that
identity is bounded and read back. Every option lives under one option
level, SOL_KACS, which the kernel dispatches ahead of the protocol's own
setsockopt/getsockopt (net/socket.c), so the options behave identically
on every socket family that supports them. SOL_KACS is 4096: far above
the upstream SOL_* range, which grows by one per new protocol, so it
cannot collide with a future Linux level. Errors: -ENOPROTOOPT for an
option this level does not define (or a get-only option passed to
setsockopt); -EOPNOTSUPP on a socket family or type KACS does not
capture identity for; -EINVAL for a short optlen or an out-of-range
value; -EFAULT for an unreadable/unwritable optval.

| Constant | Value |
|---|---|
| `SOL_KACS` | `4096` |

*getsockopt only.*

optval: int — a new token fd for the peer identity captured at
connect(), carrying fixed TOKEN_QUERY | TOKEN_IMPERSONATE access. The fd
is opened O_CLOEXEC. -ENOTCONN if the socket is not connected; -ENODATA
if it is connected but carries no captured identity.

| Constant | Value |
|---|---|
| `KACS_SO_PEER_TOKEN` | `1` |

*getsockopt / setsockopt.*

optval: __u32 KACS_IMLEVEL_* — the maximum impersonation level at which
this end's identity may be captured by the peer. Set by the client
before connect(); the default is KACS_IMLEVEL_IMPERSONATION. -EISCONN
once the socket is connected.

| Constant | Value |
|---|---|
| `KACS_SO_IMPERSONATION_LEVEL` | `2` |

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

## Tracepoint diagnostic codes

From `uapi/pkm/trace.h`.

*kacs_access_decision reason — why a KACS access hook took the return path it did.*

Emitted by the kacs:kacs_file_access / _file_open / _native_open
_inode_file_access / _inode_permission events. Verdict (allow vs deny)
is a separate signal, read from the `ret` field (0 == allow).

| Constant | Value | Notes |
|---|---|---|
| `KACS_TR_DECISION` | `0` | resolved allow/deny |
| `KACS_TR_BAD_ARGS` | `1` | NULL/zero argument guard |
| `KACS_TR_NO_ISEC` | `2` | inode has no i_security blob |
| `KACS_TR_UNMANAGED` | `3` | superblock mount policy UNMANAGED |
| `KACS_TR_PIP_CONTEXT` | `4` | current PIP context unavailable |
| `KACS_TR_NO_TOKEN` | `5` | no effective subject token |
| `KACS_TR_NO_DENTRY_ALIAS` | `6` | inode has no dentry alias yet |
| `KACS_TR_DELETE_ON_CLOSE_PENDING` | `7` | open of a delete-on-close file |
| `KACS_TR_NATIVE_STAMP` | `8` | native-open granted-access stamp |
| `KACS_TR_NATIVE_ARM` | `9` | native-open delete-on-close arm |
| `KACS_TR_STAMP` | `10` | legacy-open granted-access stamp |
| `KACS_TR_LAZY_DENTRY_RELOOKUP` | `11` | native create lazy re-lookup |
| `KACS_TR_NEGATIVE_AFTER_CREATE` | `12` | negative dentry after create |
| `KACS_TR_CHANGE_NOTIFY_PRIV` | `13` | traverse via CHANGE_NOTIFY priv |
| `KACS_TR_CHANGE_NOTIFY_PRIV_EXHAUSTED` | `14` | CHANGE_NOTIFY priv use exhausted |

*kacs_sd_cache reason — the inode security-descriptor cache outcome.*

The lookup miss codes disambiguate the three cache-absent paths that
were previously an indistinguishable NULL return (no cache / stale
generation missing-but-synthesis-required); the corrupt codes name why a
stored SD was rejected. Emitted by kacs:kacs_sd_cache_lookup / _corrupt.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SDC_HIT` | `0` | current, valid cache present |
| `KACS_SDC_MISS_NONE` | `1` | no cache attached |
| `KACS_SDC_MISS_STALE_GEN` | `2` | cache present but stale generation |
| `KACS_SDC_MISS_NEEDS_SYNTH` | `3` | missing SD requires synthesis |
| `KACS_SDC_CORRUPT_EMPTY_OR_OVERSIZE` | `4` | stored SD zero-length or oversize |
| `KACS_SDC_CORRUPT_VALIDATE_FAIL` | `5` | stored SD failed validation |

kacs_process_access reason — the outcome of a cross-process access
decision (signal, ptrace, scheduler/attribute, prlimit). The reason
distinguishes the paths that all surface as -EACCES: an SD denial, a
PIP-based denial, a denial rescued (or not) by SeDebugPrivilege, and a
PIP-dominance failure. Emitted by kacs:kacs_process_access.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PA_ALLOW` | `0` | access granted |
| `KACS_PA_BAD_ARGS` | `1` | NULL subject/target guard |
| `KACS_PA_NO_TARGET` | `2` | target has no process state/SD |
| `KACS_PA_NO_SD` | `3` | target process SD unavailable |
| `KACS_PA_SD_ERROR` | `4` | SD check failed (non-EACCES) |
| `KACS_PA_PIP_DENIED` | `5` | denied by process-integrity policy |
| `KACS_PA_DEBUG_RESCUE` | `6` | SD denial rescued by SeDebugPrivilege |
| `KACS_PA_DEBUG_DENIED` | `7` | denied; no usable SeDebugPrivilege |
| `KACS_PA_PIP_DOMINANCE` | `8` | caller PIP does not dominate target |

*kacs_exec reason — an exec/bprm credential or PIP transition.*

Distinguishes the uid/gid-change gate outcomes, the exec primary-token
derivation paths and their failures, the exec file integrity-label
lookup failures, and the two commit-time transitions. Verdict is the
`ret` field. Emitted by kacs:kacs_exec.

| Constant | Value | Notes |
|---|---|---|
| `KACS_EXEC_CREDS_ALLOW` | `0` | exec cred transition allowed |
| `KACS_EXEC_BAD_ARGS` | `1` | NULL cred/token guard |
| `KACS_EXEC_ID_CHANGE_NO_TOKEN` | `2` | uid/gid change, no subject token |
| `KACS_EXEC_ID_CHANGE_PRIV_UNSUPPORTED` | `3` | id change + ASSIGN_PRIMARY_TOKEN priv |
| `KACS_EXEC_TOKEN_NPM_DERIVED` | `4` | exec token derived via new-process-min |
| `KACS_EXEC_TOKEN_CLONE` | `5` | exec token via primary clone fallback |
| `KACS_EXEC_NPM_NO_FILE` | `6` | new-process-min needs file, none supplied |
| `KACS_EXEC_NPM_DERIVE_FAIL` | `7` | new_process_min_exec derivation failed |
| `KACS_EXEC_TOKEN_INSTALL_FAIL` | `8` | install token ref on new cred failed |
| `KACS_EXEC_TOKEN_CLONE_FAIL` | `9` | primary token clone returned NULL |
| `KACS_EXEC_INTEGRITY_NO_ISEC` | `10` | exec file inode has no i_security |
| `KACS_EXEC_INTEGRITY_NO_CACHE` | `11` | exec file SD cache absent |
| `KACS_EXEC_INTEGRITY_INVALID_SD` | `12` | exec file cached SD invalid/empty |
| `KACS_EXEC_IMPERSONATION_REVERT_FAIL` | `13` | bprm impersonation revert failed |
| `KACS_EXEC_PIP_COMMITTED` | `14` | pending exec PIP committed at commit |
| `KACS_EXEC_UMH_NOT_TCB` | `15` | usermodehelper exec below PeiosTcb trust |
| `KACS_EXEC_SIGNATURE_UNVERIFIABLE` | `16` | exec refused: signature could not be verified |

kacs_signing reason — code-signature verification outcomes and the
distinct reject reasons of the signing-material probe. Only source enum,
verified flag, PIP tier codes, file length, reason, and ret are recorded
— never key, signature, xattr, or file bytes. Emitted by
kacs:kacs_signing_verify _crypto / _probe.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SIG_UNSIGNED` | `0` | material source NONE (unsigned) |
| `KACS_SIG_BAD_KEY_TABLE` | `1` | key table malformed / bad args |
| `KACS_SIG_NO_KEY_MATCH` | `2` | no key verified the signature |
| `KACS_SIG_VERIFIED` | `3` | a key verified; trust assigned |
| `KACS_SIG_CRYPTO_UNAVAILABLE` | `4` | mldsa65 tfm allocation failed |
| `KACS_SIG_CRYPTO_MISMATCH` | `5` | set-pubkey/verify returned nonzero |
| `KACS_SIG_PROBE_FOUND` | `6` | valid signature material committed |
| `KACS_SIG_ELF_MAGIC_READ` | `7` | failed reading ELF magic |
| `KACS_SIG_ELF_SHORT_EHDR` | `8` | file too short for Elf64_Ehdr |
| `KACS_SIG_ELF_EHDR_READ` | `9` | failed reading ELF header |
| `KACS_SIG_ELF_BAD_IDENT` | `10` | unsupported e_ident class/data/version |
| `KACS_SIG_ELF_BAD_SHTABLE` | `11` | bad shentsize/shstrndx |
| `KACS_SIG_ELF_SHDRS_RANGE` | `12` | section-header table offset/len out of range |
| `KACS_SIG_ELF_SHSTR_READ` | `13` | failed reading shstrtab section header |
| `KACS_SIG_ELF_STRTAB_RANGE` | `14` | shstrtab offset/len out of range |
| `KACS_SIG_ELF_SHDR_READ` | `15` | failed reading a section header |
| `KACS_SIG_ELF_NAME_READ` | `16` | failed reading a section name |
| `KACS_SIG_ELF_BAD_SIG_SECTION` | `17` | sig section wrong type/size/range |
| `KACS_SIG_ELF_BAD_BLOB` | `18` | sig blob read failed or invalid |
| `KACS_SIG_ELF_HASH_FAIL` | `19` | hashing failed for ELF sig |
| `KACS_SIG_XATTR_BAD_BLOB` | `20` | xattr sig blob invalid |
| `KACS_SIG_XATTR_HASH_FAIL` | `21` | hashing failed for xattr sig |
| `KACS_SIG_SIZE_CHANGED` | `22` | file size changed during probe (TOCTOU) |

*kacs_socket reason — the outcome of an AF_UNIX socket SD / impersonation hook.*

Distinguishes the guard, not-applicable, and verdict paths that
otherwise collapse into an indistinguishable -EACCES. Verdict is the
`ret` field. No address, pathname, or SD bytes are recorded.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SOCK_BAD_ARGS` | `0` | NULL/guard argument rejected |
| `KACS_SOCK_NOT_UNIX` | `1` | not AF_UNIX / unsupported type |
| `KACS_SOCK_NO_SECURITY` | `2` | sock has no sk_security blob |
| `KACS_SOCK_NO_TOKEN` | `3` | no effective subject/client token |
| `KACS_SOCK_BAD_LEVEL` | `4` | invalid impersonation level |
| `KACS_SOCK_WRONG_STATE` | `5` | socket state forbids the op |
| `KACS_SOCK_NO_PEER_TOKEN` | `6` | no captured peer token present |
| `KACS_SOCK_PIP_CONTEXT` | `7` | caller PIP context unavailable |
| `KACS_SOCK_SD_DECISION` | `8` | socket-SD check produced verdict |
| `KACS_SOCK_NO_SD` | `9` | no socket SD; allowed without check |
| `KACS_SOCK_HAVE_SD` | `10` | socket SD present; check performed |
| `KACS_SOCK_ALREADY_BOUND` | `11` | socket SD already installed |
| `KACS_SOCK_BIND` | `12` | abstract-socket SD bind result |
| `KACS_SOCK_CONNECT` | `13` | unix_stream_connect result |
| `KACS_SOCK_LEVEL_SET` | `14` | impersonation level updated |
| `KACS_SOCK_OPEN_TOKEN` | `15` | open peer-token fd result |

*kacs_namespace stage — which sub-decision of a namespace-mutation hook a record describes.*

Single-decision ops report PRIMARY; multi-stage ops (link, rename,
delete fallback) tag each distinct verdict. Verdict is the `ret` field.
Never records a pathname. Emitted by the kacs:kacs_inode_* events.

| Constant | Value | Notes |
|---|---|---|
| `KACS_NS_PRIMARY` | `0` | the op's principal decision |
| `KACS_NS_PARENT_FALLBACK` | `1` | delete: parent DELETE_CHILD fallback |
| `KACS_NS_SOURCE` | `2` | link/rename source-side decision |
| `KACS_NS_DEST` | `3` | link/rename destination-parent add |
| `KACS_NS_DELETE_EXISTING` | `4` | rename: delete pre-existing dest |

kacs_psb reason — which process-security-baseline path an event marks:
mitigation activation (apply) or a W^X / LSV / PIE / prctl-lock
enforcement denial. The ok-vs-deny verdict is read from `ret`. Emitted
by kacs:kacs_psb_*.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PSB_APPLY_OK` | `0` | mitigations applied; result_bits set |
| `KACS_PSB_APPLY_NORMALIZE` | `1` | requested mask bad or unsupported (EINVAL/ENODEV) |
| `KACS_PSB_APPLY_MM_ACQUIRE` | `2` | could not acquire target mm (EACCES) |
| `KACS_PSB_APPLY_CFIF` | `3` | forward-CFI (IBT) activation failed |
| `KACS_PSB_APPLY_SML` | `4` | speculative-mitigation-lock activation failed |
| `KACS_PSB_APPLY_CFIB` | `5` | backward-CFI (shadow stack) activation failed |
| `KACS_PSB_WXP_MMAP` | `6` | W^X blocked a W+X mmap |
| `KACS_PSB_WXP_MPROTECT` | `7` | W^X blocked an mprotect transition |
| `KACS_PSB_WXP_EXISTING_VMA` | `8` | W^X activation blocked by an existing W+X vma |
| `KACS_PSB_LSV_PROBE` | `9` | LSV signing probe of the image failed |
| `KACS_PSB_LSV_VERIFY` | `10` | LSV signature not verified/trusted |
| `KACS_PSB_LSV_PIP_DOMINANCE` | `11` | LSV image PIP does not dominate process PIP |
| `KACS_PSB_PIE_ET_EXEC` | `12` | PIE blocked a non-PIE ET_EXEC image |
| `KACS_PSB_PRCTL_SML` | `13` | prctl blocked by SML lock |
| `KACS_PSB_PRCTL_CFIB` | `14` | prctl blocked by shadow-stack (CFIB) lock |
| `KACS_PSB_PRCTL_PIP` | `15` | prctl set-dumpable blocked by process PIP |

*kacs_token_ioctl cmd — which token-fd ioctl verb a record describes.*

The verdict (allow vs deny) is read from the `ret` field (0 == allow);
the access-mask-gate rejections surface as ret == -EACCES. `token` is an
opaque numeric id (never token bytes). Emitted by kacs:kacs_token_ioctl.

| Constant | Value | Notes |
|---|---|---|
| `KACS_TOK_QUERY` | `0` | KACS_IOC_QUERY |
| `KACS_TOK_ADJUST_PRIVS` | `1` | KACS_IOC_ADJUST_PRIVS |
| `KACS_TOK_ADJUST_GROUPS` | `2` | KACS_IOC_ADJUST_GROUPS |
| `KACS_TOK_DUPLICATE` | `3` | KACS_IOC_DUPLICATE |
| `KACS_TOK_INSTALL` | `4` | KACS_IOC_INSTALL |
| `KACS_TOK_RESTRICT` | `5` | KACS_IOC_RESTRICT |
| `KACS_TOK_LINK` | `6` | KACS_IOC_LINK_TOKENS |
| `KACS_TOK_GET_LINKED` | `7` | KACS_IOC_GET_LINKED_TOKEN |
| `KACS_TOK_IMPERSONATE` | `8` | KACS_IOC_IMPERSONATE |
| `KACS_TOK_ADJUST_DEFAULT` | `9` | KACS_IOC_ADJUST_DEFAULT |
| `KACS_TOK_ADJUST_INTERACTIVITY_SCOPE` | `10` | KACS_IOC_ADJUST_INTERACTIVITY_SCOPE |
| `KACS_TOK_UNKNOWN` | `11` | unrecognised ioctl verb (-ENOTTY) |

*kacs_token_ref reason — a token-fd reference lifecycle transition.*

TO_FD is a token installed into a fresh anon-inode handle; RELEASE is
the handle teardown that drops the token ref; BIND clones a token onto
an existing file; OPEN is the checked/fixed-access open path that clones
the target token. `token` is an opaque numeric id, never token bytes.
Emitted by kacs:kacs_token_ref.

| Constant | Value | Notes |
|---|---|---|
| `KACS_TREF_TO_FD` | `0` | token installed into a new fd (ret == fd) |
| `KACS_TREF_RELEASE` | `1` | token-fd released; ref dropped |
| `KACS_TREF_BIND` | `2` | token cloned + bound onto an existing file |
| `KACS_TREF_OPEN` | `3` | token cloned for a token-open path |

*kacs_logon_session reason — a session/token creation-surface outcome.*

The *_DENIED codes name the privilege-gate rejections (the value); the
plain op codes mark the successful op. Verdict is also in `ret`. No
token/spec bytes are recorded. Emitted by kacs:kacs_logon_session.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SES_CREATE` | `0` | create_logon_session published a session |
| `KACS_SES_CREATE_PRIV_DENIED` | `1` | create_logon_session: TCB privilege gate denied |
| `KACS_SES_DESTROY` | `2` | destroy_empty_logon_session outcome |
| `KACS_SES_DESTROY_PRIV_DENIED` | `3` | destroy: TCB privilege gate denied |
| `KACS_SES_CREATE_TOKEN` | `4` | create_token issued a token fd |
| `KACS_SES_CREATE_TOKEN_PRIV_DENIED` | `5` | create_token: CREATE_TOKEN privilege denied |

kacs_cred reason — a credential-security lifecycle transition: LSM cred
prepare/transfer/alloc/free, explicit token-ref install, the clone-time
primary-token lifecycle (CLONE_THREAD share vs fork deep-copy), and the
project-linux-cred rejection paths. old_token/new_token are opaque token
pointer ids (0 when absent); clone_flags is set only on the clone paths.
Verdict/outcome is the `ret` field. Emitted by kacs:kacs_cred.

| Constant | Value | Notes |
|---|---|---|
| `KACS_CRED_PREPARE` | `0` | cred_prepare token clone |
| `KACS_CRED_TRANSFER` | `1` | cred_transfer token clone |
| `KACS_CRED_ALLOC_BLANK` | `2` | cred_alloc_blank cleared sec |
| `KACS_CRED_FREE` | `3` | cred_free released token/state |
| `KACS_CRED_INSTALL_TOKEN_REF` | `4` | install token ref on a cred |
| `KACS_CRED_CLONE_THREAD_SHARE` | `5` | CLONE_THREAD shares parent primary cred |
| `KACS_CRED_CLONE_FORK_COPY` | `6` | fork deep-copies parent primary token |
| `KACS_CRED_PROJECT_UID0_BLOCKED` | `7` | uid0 projection not allowed by token |
| `KACS_CRED_PROJECT_GROUPS_ALLOC_FAIL` | `8` | groups_alloc failed (ENOMEM) |
| `KACS_CRED_PROJECT_E2BIG` | `9` | supplementary gid count > NGROUPS_MAX |

kacs_setid reason — the KACS gate on a Linux setid projection
(task_fix_setuid / _setgid / _setgroups). Each op has two distinct
denials that otherwise collapse: NO_TOKEN (-EACCES, no effective subject
token) and PRIV_GATE (-EOPNOTSUPP, holder of ASSIGN_PRIMARY_TOKEN
privilege). `flags` is the LSM_SETID_* mask (0 for setgroups). Emitted
by kacs:kacs_setid.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SETID_SETUID_NO_TOKEN` | `0` | setuid gate: no subject token |
| `KACS_SETID_SETUID_PRIV_GATE` | `1` | setuid gate: ASSIGN_PRIMARY priv |
| `KACS_SETID_SETGID_NO_TOKEN` | `2` | setgid gate: no subject token |
| `KACS_SETID_SETGID_PRIV_GATE` | `3` | setgid gate: ASSIGN_PRIMARY priv |
| `KACS_SETID_SETGROUPS_NO_TOKEN` | `4` | setgroups gate: no subject token |
| `KACS_SETID_SETGROUPS_PRIV_GATE` | `5` | setgroups gate: ASSIGN_PRIMARY priv |

*kacs_task reason — a task-security lifecycle transition.*

task_alloc reports a NO_CHILD-mitigation clone block, a process-state
inherit ENOMEM, or success; task_free marks teardown. `process_state` is
an opaque process-state pointer id (0 when absent); `clone_flags` is set
on the alloc paths. Outcome is `ret`. Emitted by kacs:kacs_task.

| Constant | Value | Notes |
|---|---|---|
| `KACS_TASK_ALLOC_NO_CHILD_BLOCKED` | `0` | clone blocked by NO_CHILD mitigation |
| `KACS_TASK_ALLOC_INHERIT_ENOMEM` | `1` | process-state inherit failed (ENOMEM) |
| `KACS_TASK_ALLOC` | `2` | task_alloc completed |
| `KACS_TASK_FREE` | `3` | task_free teardown |

*kacs_primary_install reason — a primary-token / impersonation credential transition.*

Distinguishes the install commit, the user-SID-change process-SD
reallocation and its ENOMEM, the commit_creds apply, the impersonation
override/revert, and the sibling-thread taskwork requeue/failure.
old_primary and new_primary are opaque token identity ids (never token
bytes). Verdict is the `ret` field. Emitted by
kacs:kacs_primary_install.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PRIM_INSTALL_OK` | `0` | primary token install committed |
| `KACS_PRIM_SD_REALLOC` | `1` | user-SID changed; process SD reallocated |
| `KACS_PRIM_SD_ALLOC_FAIL` | `2` | process SD realloc failed (ENOMEM) |
| `KACS_PRIM_APPLY_COMMIT` | `3` | new real creds committed (commit_creds) |
| `KACS_PRIM_IMPERSONATE_INSTALL` | `4` | impersonation token installed (override_creds) |
| `KACS_PRIM_IMPERSONATE_REVERT` | `5` | impersonation reverted (revert_creds) |
| `KACS_PRIM_SIBLING_REQUEUE` | `6` | queued sibling install re-queued on ENOMEM |
| `KACS_PRIM_SIBLING_FAILED` | `7` | queued sibling install failed after apply |

kacs_process_token_open reason — the outcome of opening a process/thread
primary or effective token (kacs_open_process_token / _thread_token and
the proc inspection files). Distinguishes the bad access-mask reject,
the no-target-token path, the process access-check denial, the self vs
cross inspection verdicts, and the successful open.
subject_token/target_token are opaque token identity ids (0 when unknown
at the emit site); access_mask is the requested mask. Verdict is `ret`
(>=0 fd == allow). Emitted by kacs:kacs_process_token_open.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PTO_OPEN_OK` | `0` | token fd opened |
| `KACS_PTO_BAD_ARGS` | `1` | NULL subject/state/task guard |
| `KACS_PTO_NO_TARGET` | `2` | target has no token |
| `KACS_PTO_BAD_ACCESS` | `3` | invalid access mask rejected |
| `KACS_PTO_ACCESS_DENIED` | `4` | process access check denied |
| `KACS_PTO_SELF` | `5` | self-target inspection allowed |
| `KACS_PTO_CROSS` | `6` | cross-process inspection authorized |

*kacs_process_state reason — a process-state / process-SD lifecycle or PIP transition.*

Covers process-state alloc/free, the CLONE_THREAD share vs fork
inheritance split, the no-child clone block, the pending-exec-PIP
stage/commit and dumpable hardening, and the process-SD
alloc/wrap/replace primitives. process_state is an opaque state-object
id (0 when none in scope, e.g. the process-SD primitives);
pip_type/pip_trust carry the PIP tier. `ret` is the outcome (0 == ok).
No token or SD bytes. Emitted by kacs:kacs_process_state.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PST_ALLOC` | `0` | process state allocated |
| `KACS_PST_ALLOC_FAIL` | `1` | process state alloc failed (ENOMEM) |
| `KACS_PST_FREE` | `2` | process state freed (refcount hit 0) |
| `KACS_PST_INHERIT_SHARE` | `3` | CLONE_THREAD: parent state shared |
| `KACS_PST_INHERIT_FORK` | `4` | fork: new state allocated from parent |
| `KACS_PST_EXEC_PIP_STAGE` | `5` | pending exec PIP staged |
| `KACS_PST_EXEC_PIP_COMMIT` | `6` | pending exec PIP committed to state |
| `KACS_PST_DUMPABLE` | `7` | exec dumpable hardened by PIP |
| `KACS_PST_CLONE_BLOCKED_NOCHILD` | `8` | clone blocked by NO_CHILD mitigation |
| `KACS_PST_SD_ALLOC` | `9` | default process SD allocated |
| `KACS_PST_SD_ALLOC_FAIL` | `10` | process/socket SD alloc failed |
| `KACS_PST_SD_WRAP_FAIL` | `11` | process SD wrapper alloc failed (ENOMEM) |
| `KACS_PST_SD_REPLACE` | `12` | process SD replaced on state |
| `KACS_PST_SOCKET_SD_ALLOC` | `13` | default socket SD allocated |

*kacs_mount_policy reason — the outcome of a mount-policy set (TCB-gated) or get.*

SET_OK marks a committed policy change (generation bumped); the guard
codes name the pre-commit rejects that otherwise collapse into a bare
-EINVAL/-EOPNOTSUPP/-EPERM. GET_OK/GET_NO_SECURITY are the snapshot
paths. Verdict is also in `ret`. Emitted by kacs:kacs_mount_policy_set /
_get.

| Constant | Value | Notes |
|---|---|---|
| `KACS_MP_SET_OK` | `0` | policy committed; generation bumped |
| `KACS_MP_BAD_ARGS` | `1` | NULL subject/sb/args guard (EINVAL) |
| `KACS_MP_NO_SECURITY` | `2` | superblock has no s_security (EOPNOTSUPP) |
| `KACS_MP_UNMANAGED` | `3` | magic-derived UNMANAGED; not settable (EOPNOTSUPP) |
| `KACS_MP_VALIDATE` | `4` | mount-policy args validation failed (EINVAL) |
| `KACS_MP_TEMPLATE_INVALID` | `5` | template SD bytes failed validation (EINVAL) |
| `KACS_MP_TCB_DENIED` | `6` | SeTcbPrivilege gate denied (EPERM) |
| `KACS_MP_GET_OK` | `7` | policy snapshot returned |
| `KACS_MP_GET_NO_SECURITY` | `8` | get: no s_security; magic-derived policy returned |
| `KACS_MP_FIXED_POLICY` | `9` | filesystem fixes its policy class (EOPNOTSUPP) |

kacs_sd_syscall target_kind — which SD-bearing object a query/set record
describes, resolved by the get_sd/set_sd syscall target-kind
fallthrough. ACCESS_CHECK tags the AccessCheck ingress events
(kacs_access_check*), whose other scalar fields are 0 at the ingress
boundary.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SDS_KIND_TOKEN` | `0` | token-fd target |
| `KACS_SDS_KIND_FILE` | `1` | file/inode target |
| `KACS_SDS_KIND_PROCESS` | `2` | pidfd process target |
| `KACS_SDS_KIND_PATH` | `3` | path-resolved file target |
| `KACS_SDS_KIND_ACCESS_CHECK` | `4` | AccessCheck ingress (not an SD get/set) |

*kacs_sd_syscall reason — the outcome of an SD query/set core.*

QUERY_OK/SET_OK are the success paths; the remaining codes name the
guard / denial paths that otherwise surface as an indistinguishable
-EINVAL/-EACCES/-EOPNOTSUPP. Verdict is also in `ret`. Emitted by
kacs:kacs_sd_query / _set.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SDS_QUERY_OK` | `0` | SD subset extracted and returned |
| `KACS_SDS_SET_OK` | `1` | SD merged/replaced |
| `KACS_SDS_BAD_ARGS` | `2` | NULL/zero argument guard (EINVAL) |
| `KACS_SDS_UNMANAGED` | `3` | superblock UNMANAGED (EOPNOTSUPP) |
| `KACS_SDS_ACCESS_DENIED` | `4` | SD access check denied (EACCES) |
| `KACS_SDS_NO_SD` | `5` | target has no usable SD (EACCES) |
| `KACS_SDS_RESTORE_BYPASS` | `6` | set via SeRestorePrivilege bypass |
| `KACS_SDS_QUERY_FAIL` | `7` | subset extraction failed after auth |

kacs_access_check reason — the AccessCheck kernel-ingress outcome, above
the closed Slice 15 ABI bridge. OK is a completed ingress; the remaining
codes name the ingress-time rejects (token-eval-context gate, token
resolution, and caap-cache lock acquisition). Verdict is also in `ret`.
Emitted by kacs:kacs_access_check / _list.

| Constant | Value | Notes |
|---|---|---|
| `KACS_ACK_OK` | `0` | ingress dispatched to the ABI bridge |
| `KACS_ACK_EVAL_CONTEXT` | `1` | token-eval-context gate denied (EACCES) |
| `KACS_ACK_TOKEN_RESOLVE` | `2` | token/args resolution failed |
| `KACS_ACK_CAAP_LOCK_FAIL` | `3` | caap-cache lock acquisition failed |

*kacs_file_snapshot op — which snapshot-grant file operation an event marks.*

The allow-vs-deny verdict is read from `ret`; `reason` names why a deny
path was taken. Emitted by kacs:kacs_file_snapshot (file_access.c).

| Constant | Value | Notes |
|---|---|---|
| `KACS_FSOP_ACCESS` | `0` | generic snapshot-grant access check |
| `KACS_FSOP_PERMISSION` | `1` | file_permission hook |
| `KACS_FSOP_IOCTL` | `2` | file ioctl snapshot |
| `KACS_FSOP_LOCK` | `3` | file lock snapshot |
| `KACS_FSOP_FCNTL` | `4` | file fcntl snapshot |
| `KACS_FSOP_TRUNCATE` | `5` | file truncate snapshot |
| `KACS_FSOP_FALLOCATE` | `6` | file fallocate snapshot |
| `KACS_FSOP_MMAP` | `7` | file mmap snapshot |
| `KACS_FSOP_MPROTECT` | `8` | file mprotect snapshot |
| `KACS_FSOP_WRITE_INTENT` | `9` | write-intent snapshot |
| `KACS_FSOP_SYSFS_WRITE_GATE` | `10` | unmanaged sysfs write gate |

*kacs_file_snapshot reason — why a snapshot-grant op took its return path.*

DECISION is the resolved allow/deny (verdict in `ret`); the remaining
codes name the distinct deny causes. Emitted by kacs:kacs_file_snapshot.

| Constant | Value | Notes |
|---|---|---|
| `KACS_FSR_DECISION` | `0` | resolved allow/deny (grant compare) |
| `KACS_FSR_SIGNED_EXEC` | `1` | signed-exec content mutation denied |
| `KACS_FSR_GRANT_DENY` | `2` | granted access lacked required right |
| `KACS_FSR_APPEND_DENY` | `3` | append/write intent lacked write grant |
| `KACS_FSR_UNMANAGED_SYSFS` | `4` | unmanaged fd: sysfs write gate applied |
| `KACS_FSR_AUDIT_EMIT_FAIL` | `5` | continuous-audit emit failed |

*kacs_metadata reason — the file-metadata (getattr/setattr/xattr/getsecurity) decision path.*

DECISION/CONSUME_HIT/BEGIN_BUSY mark the begin/consume decision
lifecycle; the remaining codes name the distinct deny reasons of the
xattr setattr hooks. `op_class` carries the internal
PKM_KACS_METADATA_OP_* value; `matched` is the consume match flag.
Emitted by kacs:kacs_metadata (file_metadata.c).

| Constant | Value | Notes |
|---|---|---|
| `KACS_META_DECISION` | `0` | generic metadata decision |
| `KACS_META_CONSUME_HIT` | `1` | consumed a pre-staged decision |
| `KACS_META_BEGIN_BUSY` | `2` | begin failed: a decision already active |
| `KACS_META_CANONICAL_SD` | `3` | canonical SD xattr access denied |
| `KACS_META_CAPS_XATTR` | `4` | capability xattr mutation denied (EPERM) |
| `KACS_META_ACL` | `5` | POSIX ACL xattr denied |
| `KACS_META_SIGNED_EXEC` | `6` | signed-exec xattr/size mutation denied |
| `KACS_META_BAD_ARGS` | `7` | NULL name / dentry guard |
| `KACS_META_INTERNAL_SD` | `8` | internal SD read/write re-entry allowed |
| `KACS_META_GETSECURITY` | `9` | inode_getsecurity outcome |

kacs_native_open_ext reason — a widening decision inside the native
(kacs_open) create/open machinery. The PREPARE_* codes name the arg-
validation reject buckets of pkm_kacs_prepare_native_open; RESOLVE /
BUILD_CREATED_SD DELETE_ON_CLOSE_ARM name the later stage outcomes
(verdict in `ret`). Emitted by kacs:kacs_native_open_ext
(native_open.c).

| Constant | Value | Notes |
|---|---|---|
| `KACS_NOX_PREPARE_OK` | `0` | prepare accepted the request |
| `KACS_NOX_PREPARE_BAD_FLAGS` | `1` | flags/create_options/__pad rejected |
| `KACS_NOX_PREPARE_BAD_SD_ARGS` | `2` | sd_ptr/sd_len/disposition-sd combo bad |
| `KACS_NOX_PREPARE_BAD_DISPOSITION` | `3` | create_disposition out of range |
| `KACS_NOX_PREPARE_BAD_ACCESS` | `4` | desired-access mask invalid/empty |
| `KACS_NOX_PREPARE_UNSUPPORTED` | `5` | valid but unsupported combination |
| `KACS_NOX_RESOLVE` | `6` | resolve-existing-path outcome |
| `KACS_NOX_BUILD_CREATED_SD` | `7` | build-created-file-SD outcome |
| `KACS_NOX_DELETE_ON_CLOSE_ARM` | `8` | delete-on-close arm outcome |

*kacs_object reason — which object-lifecycle verdict a record marks.*

Only the high-value transitions are traced (pure inode/file/sb
alloc/free are not). `ret` is the outcome (0 == ok). Emitted by
kacs:kacs_object.

| Constant | Value | Notes |
|---|---|---|
| `KACS_OBJ_DELETE_ON_CLOSE_UNLINK` | `0` | file_release delete-on-close unlink attempt |
| `KACS_OBJ_SIGNED_EXEC_PIN` | `1` | inode pinned as signed-exec (immutable) |
| `KACS_OBJ_SIGNED_EXEC_MUTATION_BLOCKED` | `2` | content mutation of a signed-exec-pinned inode denied |

*kacs_securityfs reason — which securityfs endpoint path a record marks.*

The sessions_read codes disambiguate the deny rungs that otherwise
collapse into an errno; open_self / init report the endpoint outcome.
Verdict is `ret`. Emitted by kacs:kacs_securityfs.

| Constant | Value | Notes |
|---|---|---|
| `KACS_SFS_LOGON_SESSIONS_NO_TOKEN` | `0` | sessions read: no effective subject token |
| `KACS_SFS_LOGON_SESSIONS_PIP_CONTEXT` | `1` | sessions read: caller PIP context unavailable |
| `KACS_SFS_LOGON_SESSIONS_ACCESS_CHECK` | `2` | sessions read: rust access check denied |
| `KACS_SFS_OPEN_SELF` | `3` | open of kacs/self self-token file outcome |
| `KACS_SFS_INIT` | `4` | securityfs kacs/ endpoint init outcome |

*kacs_caap reason — which CAAP policy-cache path a record marks.*

SET carries the post-set cache_len (an insert grows it; an evict/replace
may shrink it); INIT/DESTROY are cache lifecycle; TCB_GATE is the
SeTcbPrivilege gate deny. Emitted by kacs:kacs_caap. No SID or spec
bytes — lengths only.

| Constant | Value | Notes |
|---|---|---|
| `KACS_CAAP_TCB_GATE` | `0` | SeTcbPrivilege gate denied the caller |
| `KACS_CAAP_SET` | `1` | cache set (insert/evict); cache_len is post-set count |
| `KACS_CAAP_INIT` | `2` | CAAP cache created |
| `KACS_CAAP_DESTROY` | `3` | CAAP cache destroyed |

kacs_capability reason — the capability->privilege gate verdicts and the
capability LSM-hook outcomes. ALLOW_GRANT is an auto-granted allow-cap;
HARD_DENY is the SETPCAP/SETFCAP/MAC_OVERRIDE hard block;
PRIV_NOT_ENABLED USE_MARK_FAIL are the mapped-privilege gate failures;
CAPSET / PRCTL_GUARD CAPABLE / CAPGET report the corresponding hook
outcome. Emitted by kacs:kacs_capability. Verdict is `ret`.

| Constant | Value | Notes |
|---|---|---|
| `KACS_CAP_ALLOW_GRANT` | `0` | allow-cap auto-granted (no privilege needed) |
| `KACS_CAP_HARD_DENY` | `1` | SETPCAP/SETFCAP/MAC_OVERRIDE hard-denied |
| `KACS_CAP_PRIV_NOT_ENABLED` | `2` | mapped privilege not enabled on token |
| `KACS_CAP_USE_MARK_FAIL` | `3` | privilege use-mark failed |
| `KACS_CAP_CAPSET` | `4` | capset core outcome |
| `KACS_CAP_PRCTL_GUARD` | `5` | prctl capability-guard outcome |
| `KACS_CAP_CAPABLE` | `6` | capable() hook guard-deny outcome |
| `KACS_CAP_CAPGET` | `7` | capget for-task outcome |

kacs_privilege reason — the require_enabled_privilege gate rungs plus
two standalone privilege-path markers. NULL_OR_ZERO is a null-
token/zero-mask guard; NOT_ENABLED / USE_MARK_FAIL are the gate
failures; CHANGE_NOTIFY marks the open_by_handle_at
SeChangeNotifyPrivilege check outcome; RCU_ENOMEM_ FALLBACK marks the
deferred-free ENOMEM synchronize_rcu fallback. Emitted by
kacs:kacs_privilege. Verdict is `ret`.

| Constant | Value | Notes |
|---|---|---|
| `KACS_PRIV_NULL_OR_ZERO` | `0` | null token or zero privilege mask |
| `KACS_PRIV_NOT_ENABLED` | `1` | privilege not enabled on token |
| `KACS_PRIV_USE_MARK_FAIL` | `2` | privilege use-mark failed |
| `KACS_PRIV_CHANGE_NOTIFY` | `3` | open_by_handle_at CHANGE_NOTIFY gate outcome |
| `KACS_PRIV_RCU_ENOMEM_FALLBACK` | `4` | deferred-free kmalloc failed; sync-rcu fallback |

*kacs_tlp reason — the trusted-launch-path decisions.*

CHECK_PATH marks a no-prefix-match executable-transition deny (path_len
+ prefix_count only, NEVER path or prefix bytes); REPLACE marks a
prefix-table replacement. Emitted by kacs:kacs_tlp. Verdict is `ret`.

| Constant | Value | Notes |
|---|---|---|
| `KACS_TLP_CHECK_PATH` | `0` | executable transition denied: no prefix match |
| `KACS_TLP_REPLACE` | `1` | TLP prefix table replaced |

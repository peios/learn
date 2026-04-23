---
title: ABI Reference
---

Normative byte-level ABI reference for the KACS v0.20 kernel/userspace boundary. All values are little-endian on x86_64 unless stated otherwise. An independent implementor can write compatible code from this page alone.

## 1. Syscall Table

KACS syscalls occupy the 1000-1099 range in the x86_64 syscall table. The event subsystem uses 1050.

| Number | Name | Parameters | Return |
|--------|------|-----------|--------|
| 1000 | `kacs_open_self_token` | `unsigned int flags`, `u32 access_mask` | Token fd (>= 0) or `-errno` |
| 1001 | `kacs_open_process_token` | `int pidfd`, `u32 access_mask` | Token fd (>= 0) or `-errno` |
| 1002 | `kacs_open_thread_token` | `int pidfd`, `int tid`, `u32 access_mask` | Token fd (>= 0) or `-errno` |
| 1003 | `kacs_create_token` | `const void __user *spec`, `size_t len` | Token fd (>= 0) or `-errno` |
| 1004 | `kacs_create_session` | `const void __user *spec`, `size_t len` | Session ID (u64, >= 0) or `-errno` |
| 1005 | `kacs_set_psb` | `int pidfd`, `u32 mitigations` | 0 or `-errno` |
| 1010 | `kacs_open_peer_token` | `int conn_fd` | Token fd (>= 0) or `-errno` |
| 1011 | `kacs_impersonate_peer` | `int conn_fd` | 0 or `-errno` |
| 1012 | `kacs_revert` | (none) | 0 |
| 1013 | `kacs_set_impersonation_level` | `int sock_fd`, `u32 level` | 0 or `-errno` |
| 1020 | `kacs_open` | `int dirfd`, `const char __user *path`, `struct kacs_open_how __user *uhow`, `size_t howsize`, `u32 __user *status_out` | File fd (>= 0) or `-errno` |
| 1021 | `kacs_get_sd` | `int dirfd`, `const char __user *path`, `u32 security_info`, `void __user *buf`, `u32 buf_len`, `u32 flags` | SD size in bytes (>= 0) or `-errno`. Always returns the total SD size, even on probe calls (buf_len=0). |
| 1022 | `kacs_set_sd` | `int dirfd`, `const char __user *path`, `u32 security_info`, `const void __user *sd_buf`, `u32 sd_len`, `u32 flags` | 0 or `-errno` |
| 1023 | `kacs_access_check` | `struct kacs_access_check_args __user *uargs` | Granted mask (>= 0) or `-errno` |
| 1024 | `kacs_access_check_list` | `struct kacs_access_check_args __user *uargs`, `struct kacs_node_result __user *results`, `u32 results_count` | 0 or `-errno` |
| 1025 | `kacs_set_caap` | `const void __user *policy_sid`, `u32 policy_sid_len`, `const void __user *spec`, `u32 spec_len` | 0 or `-errno` |
| 1050 | `event_emit` | `const void __user *body`, `u32 body_len` | 0 or `-errno` |

### Syscall 1000: kacs_open_self_token flags

| Flag | Value | Meaning |
|------|-------|---------|
| `KACS_REAL_TOKEN` | `0x01` | Return the primary token even if the thread is impersonating |

### Syscall 1005: kacs_set_psb mitigations bitmask

| Flag | Value | Meaning |
|------|-------|---------|
| `KACS_MIT_WXP` | `0x001` | Write-XOR-Execute |
| `KACS_MIT_TLP` | `0x002` | Trusted Library Paths |
| `KACS_MIT_LSV` | `0x004` | Library Signature Verification |
| `KACS_MIT_CFI` | `0x008` | Legacy: sets both CFIF + CFIB |
| `KACS_MIT_UI_ACCESS` | `0x010` | UI interaction (reserved) |
| `KACS_MIT_NO_CHILD` | `0x020` | Cannot fork (one-way) |
| `KACS_MIT_CFIF` | `0x040` | Forward-edge CFI (IBT) |
| `KACS_MIT_CFIB` | `0x080` | Backward-edge CFI (shadow stack) |
| `KACS_MIT_PIE` | `0x100` | Reject non-PIE binaries at exec |
| `KACS_MIT_SML` | `0x200` | Speculation mitigation lock |
| `KACS_MIT_ALL` | `0x3FF` | All valid flags OR'd |

### PIP type constants

| Constant | Value |
|----------|-------|
| `PIP_TYPE_NONE` | `0` |
| `PIP_TYPE_PROTECTED` | `512` |
| `PIP_TYPE_ISOLATED` | `1024` |

### Syscall 1013: Impersonation levels

| Constant | Value |
|----------|-------|
| `KACS_LEVEL_ANONYMOUS` | `0` |
| `KACS_LEVEL_IDENTIFICATION` | `1` |
| `KACS_LEVEL_IMPERSONATION` | `2` |
| `KACS_LEVEL_DELEGATION` | `3` |

### Syscall 1020: kacs_open create dispositions

| Constant | Value | Behavior |
|----------|-------|----------|
| `KACS_FILE_SUPERSEDE` | `0` | Delete existing + create new |
| `KACS_FILE_OPEN` | `1` | Open existing, fail if not found |
| `KACS_FILE_CREATE` | `2` | Create new, fail if exists |
| `KACS_FILE_OPEN_IF` | `3` | Open if exists, create if not |
| `KACS_FILE_OVERWRITE` | `4` | Truncate existing, fail if not found |
| `KACS_FILE_OVERWRITE_IF` | `5` | Truncate if exists, create if not |

### Syscall 1023: Privilege intent flags

| Constant | Value | Meaning |
|----------|-------|---------|
| `KACS_BACKUP_INTENT` | `0x01` | Request backup privilege evaluation |
| `KACS_RESTORE_INTENT` | `0x02` | Request restore privilege evaluation |

### Syscall 1021/1022: SECURITY_INFORMATION flags

| Constant | Value |
|----------|-------|
| `OWNER_SECURITY_INFORMATION` | `0x01` |
| `GROUP_SECURITY_INFORMATION` | `0x02` |
| `DACL_SECURITY_INFORMATION` | `0x04` |
| `SACL_SECURITY_INFORMATION` | `0x08` |
| `LABEL_SECURITY_INFORMATION` | `0x10` |

## 2. Ioctl Commands

All ioctls are issued on a KACS token fd (an anon_inode with `kacs-token` name and `O_CLOEXEC`).

**`KACS_IOC_MAGIC`** = `'K'` (0x4B)

| Name | Direction | Number | Arg Struct | Required Access |
|------|-----------|--------|-----------|----------------|
| `KACS_IOC_QUERY` | `_IOWR` | 0 | `struct kacs_query_args` | `KACS_TOKEN_QUERY` |
| `KACS_IOC_ADJUST_PRIVS` | `_IOW` | 1 | `struct kacs_adjust_privs_args` | `KACS_TOKEN_ADJUST_PRIVS` |
| `KACS_IOC_DUPLICATE` | `_IOWR` | 2 | `struct kacs_duplicate_args` | `KACS_TOKEN_DUPLICATE` |
| `KACS_IOC_INSTALL` | `_IO` | 3 | (none) | `KACS_TOKEN_ASSIGN_PRIMARY` |
| `KACS_IOC_RESTRICT` | `_IOWR` | 4 | `struct kacs_restrict_args` | `KACS_TOKEN_DUPLICATE` |
| `KACS_IOC_LINK_TOKENS` | `_IOW` | 5 | `struct kacs_link_tokens_args` | Both `elevated_fd` and `filtered_fd` require `KACS_TOKEN_DUPLICATE`. Caller requires SeTcbPrivilege. |
| `KACS_IOC_GET_LINKED_TOKEN` | `_IOWR` | 6 | `struct kacs_get_linked_token_args` | `KACS_TOKEN_QUERY` |
| `KACS_IOC_ADJUST_GROUPS` | `_IOW` | 7 | `struct kacs_adjust_groups_args` | `KACS_TOKEN_ADJUST_GROUPS` |
| `KACS_IOC_IMPERSONATE` | `_IO` | 8 | (none) | `KACS_TOKEN_IMPERSONATE` |
| `KACS_IOC_ADJUST_DEFAULT` | `_IOW` | 9 | `struct kacs_adjust_default_args` | `KACS_TOKEN_ADJUST_DEFAULT` |
| `KACS_IOC_ADJUST_SESSIONID` | `_IOW` | 10 | `u32` (session ID value) | `KACS_TOKEN_ADJUST_SESSIONID` + `SeTcbPrivilege` |

## 3. Token Query Classes

Passed as the `token_class` field in `struct kacs_query_args`. The query populates a caller-supplied buffer via the `buf_ptr`/`buf_len` fields. When `buf_ptr` is 0 or `buf_len` is 0, the kernel returns the required buffer size in `buf_len` (size query).

| Class | Value | Name | Payload layout |
|-------|-------|------|----------------|
| 1 | `0x01` | `TOKEN_CLASS_USER` | Binary SID (variable length: `8 + 4*SubAuthorityCount` bytes) |
| 2 | `0x02` | `TOKEN_CLASS_GROUPS` | `[count:u32le]` then per group: `[sid_len:u32le][sid_bytes][attrs:u32le]` |
| 3 | `0x03` | `TOKEN_CLASS_PRIVILEGES` | `[present:u64le][enabled:u64le][enabled_by_default:u64le][used:u64le]` (32 bytes) |
| 4 | `0x04` | `TOKEN_CLASS_TYPE` | `[type:u32le]` — 1=Primary, 2=Impersonation (4 bytes) |
| 5 | `0x05` | `TOKEN_CLASS_INTEGRITY_LEVEL` | Binary integrity SID: `S-1-16-{rid}` in SID binary format |
| 6 | `0x06` | `TOKEN_CLASS_OWNER` | Binary SID — resolved from `owner_sid_index` (0=user, N=groups[N-1]) |
| 7 | `0x07` | `TOKEN_CLASS_PRIMARY_GROUP` | Binary SID — resolved from `primary_group_index` (0=user, N=groups[N-1]) |
| 8 | `0x08` | `TOKEN_CLASS_SESSION_ID` | `[interactive_session_id:u32le]` (4 bytes) |
| 9 | `0x09` | `TOKEN_CLASS_RESTRICTED_SIDS` | Same format as class 2. `[count:u32le]` then per SID: `[sid_len:u32le][sid_bytes][attrs:u32le]`. Count=0 if unrestricted. |
| 10 | `0x0A` | `TOKEN_CLASS_SOURCE` | `[name:8 bytes][source_id:u64le]` (16 bytes) |
| 11 | `0x0B` | `TOKEN_CLASS_STATISTICS` | `[token_id:u64le][auth_id:u64le][modified_id:u64le][type:u32le][_pad:u32le][expiration:u64le]` (40 bytes) |
| 12 | `0x0C` | `TOKEN_CLASS_ORIGIN` | `[origin:u64le]` (8 bytes) |
| 13 | `0x0D` | `TOKEN_CLASS_ELEVATION_TYPE` | `[type:u32le]` — 1=Default, 2=Full, 3=Limited (4 bytes) |
| 14 | `0x0E` | `TOKEN_CLASS_DEVICE_GROUPS` | Same format as class 2. Count=0 if no device groups. |
| 15 | `0x0F` | `TOKEN_CLASS_APPCONTAINER_SID` | Binary SID (confinement SID). Empty if not confined. |
| 16 | `0x10` | `TOKEN_CLASS_CAPABILITIES` | Same format as class 2 (confinement capabilities). |
| 17 | `0x11` | `TOKEN_CLASS_MANDATORY_POLICY` | `[policy:u32le]` — NO_WRITE_UP=0x0001, NEW_PROCESS_MIN=0x0002 (4 bytes) |
| 18 | `0x12` | `TOKEN_CLASS_LOGON_TYPE` | `[logon_type:u32le]` — Interactive=2, Network=3, Batch=4, Service=5, NetworkCleartext=8, NewCredentials=9 (4 bytes) |
| 19 | `0x13` | `TOKEN_CLASS_LOGON_SID` | Binary SID: `S-1-5-5-{high}-{low}` in SID binary format |
| 20 | `0x14` | `TOKEN_CLASS_DEFAULT_DACL` | Binary ACL in self-relative format. Empty if no default DACL. |
| 21 | `0x15` | `TOKEN_CLASS_IMPERSONATION_LEVEL` | `[level:u32le]` — Anonymous=0, Identification=1, Impersonation=2, Delegation=3 (4 bytes). Primary tokens always return Anonymous (0). |

## 4. Struct Layouts

All structs use natural alignment. Sizes assume LP64 (x86_64).

### struct kacs_access_check_args

Total size: **136 bytes**. Minimum accepted size (v1): **40 bytes** (`KACS_ACCESS_CHECK_ARGS_V1_SIZE`). Fields beyond the caller's struct size are zero-initialized (audit context, continuous_audit_out, staging_mismatch_out all default to null).

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `size` | `u32` | `sizeof(struct)` for versioning |
| 4 | 4 | `token_fd` | `s32` | Token to evaluate (-1 = calling thread's effective token) |
| 8 | 8 | `sd_ptr` | `u64` | Userspace pointer to self-relative SD |
| 16 | 4 | `sd_len` | `u32` | Length of SD in bytes |
| 20 | 4 | `desired_access` | `u32` | Requested access rights |
| 24 | 4 | `generic_read` | `u32` | Object-specific GenericMapping: read |
| 28 | 4 | `generic_write` | `u32` | Object-specific GenericMapping: write |
| 32 | 4 | `generic_execute` | `u32` | Object-specific GenericMapping: execute |
| 36 | 4 | `generic_all` | `u32` | Object-specific GenericMapping: all |
| 40 | 8 | `self_sid_ptr` | `u64` | PRINCIPAL_SELF substitution SID (0 = none) |
| 48 | 4 | `self_sid_len` | `u32` | Length of self SID |
| 52 | 4 | `privilege_intent` | `u32` | `KACS_BACKUP_INTENT` / `KACS_RESTORE_INTENT` |
| 56 | 8 | `object_tree_ptr` | `u64` | OBJECT_TYPE_LIST array (0 = none) |
| 64 | 4 | `object_tree_count` | `u32` | Number of object type entries |
| 68 | 4 | `_pad0` | `u32` | Reserved, must be 0 (alignment padding) |
| 72 | 8 | `local_claims_ptr` | `u64` | Conditional ACE claims (0 = none) |
| 80 | 4 | `local_claims_len` | `u32` | Length of local claims |
| 84 | 4 | `_pad1` | `u32` | Reserved, must be 0 (alignment padding) |
| 88 | 8 | `granted_out_ptr` | `u64` | Output: pointer to u32 for granted mask. 0 = not used. In scalar syscall 1023, the same granted mask is also returned directly in the syscall return value. In syscall 1024 (`kacs_access_check_list`), this pointer receives the root node's granted mask (the intersection value) because the syscall return value is 0/`-errno`. A bad pointer returns -EFAULT. |
| 96 | 4 | `pip_type` | `u32` | PIP type for evaluation. 0 = use the calling process's pip_type (set at exec from binary signature). |
| 100 | 4 | `pip_trust` | `u32` | PIP trust for evaluation. 0 = use the calling process's pip_trust (set at exec from binary signature). |
| 104 | 8 | `audit_context_ptr` | `u64` | Pointer to opaque audit context blob (0 = no object identification in audit events). |
| 112 | 4 | `audit_context_len` | `u32` | Length of audit context blob in bytes. Max 4096. |
| 116 | 4 | `_pad2` | `u32` | Reserved, must be 0 (alignment padding). |
| 120 | 8 | `continuous_audit_out_ptr` | `u64` | Output: pointer to u32 for continuous audit mask from alarm ACEs. 0 = not used. Written even on -EACCES. |
| 128 | 8 | `staging_mismatch_out_ptr` | `u64` | Output: pointer to u32 for staging mismatch flag. 0 = not used. Written as 1 if CAAP staged result differs from effective. In scalar mode this includes scalar grant deltas and audit deltas. In result-list mode it is also written as 1 if any node's staged granted mask differs from that node's effective granted mask. |

Total size: **136 bytes**.

### struct kacs_query_args

Total size: **16 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `token_class` | `u32` | `TOKEN_CLASS_*` constant |
| 4 | 4 | `buf_len` | `u32` | In: buffer size. Out: required/actual size |
| 8 | 8 | `buf_ptr` | `u64` | Userspace pointer to output buffer |

### struct kacs_adjust_privs_args

Total size: **24 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `count` | `u32` | Number of `kacs_priv_entry` elements (max 64) |
| 4 | 4 | `_pad` | `u32` | Reserved, must be 0 (alignment padding) |
| 8 | 8 | `data_ptr` | `u64` | Userspace pointer to `kacs_priv_entry[]` array |
| 16 | 8 | `previous_enabled` | `u64` | Output: enabled bitmask before adjustment |

### struct kacs_priv_entry

Total size: **8 bytes**. Array element pointed to by `kacs_adjust_privs_args.data_ptr`.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `luid` | `u32` | Privilege bit position (0-63) |
| 4 | 4 | `attributes` | `u32` | `SE_PRIVILEGE_ENABLED` (0x02) / `SE_PRIVILEGE_REMOVED` (0x04) / 0 (disable) |

### struct kacs_duplicate_args

Total size: **16 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `access_mask` | `u32` | Access rights for the new handle |
| 4 | 4 | `token_type` | `u32` | 1 = Primary, 2 = Impersonation |
| 8 | 4 | `impersonation_level` | `u32` | 0-3 (Anonymous through Delegation) |
| 12 | 4 | `result_fd` | `s32` | Output: fd for the new token |

### struct kacs_restrict_args

Total size: **40 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 8 | `privs_to_delete` | `u64` | Bitmask of privileges to permanently remove |
| 8 | 4 | `num_deny_indices` | `u32` | Count of group indices to flip to deny-only |
| 12 | 4 | `num_restrict_sids` | `u32` | Count of restricting SIDs to add |
| 16 | 4 | `data_len` | `u32` | Total length of variable data at `data_ptr` |
| 20 | 4 | `flags` | `u32` | Bit 0: `KACS_RESTRICT_WRITE_RESTRICTED` (0x01) — enable write-restricted mode + user_deny_only. All other bits reserved, must be 0. |
| 24 | 8 | `data_ptr` | `u64` | Userspace pointer: `u32[]` deny indices, then binary SIDs |
| 32 | 4 | `result_fd` | `s32` | Output: new restricted token fd |
| 36 | 4 | (implicit padding) | | Struct padding to 40 bytes |

### struct kacs_link_tokens_args

Total size: **16 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `elevated_fd` | `s32` | fd to the elevated/full token |
| 4 | 4 | `filtered_fd` | `s32` | fd to the filtered/limited token |
| 8 | 8 | `session_id` | `u64` | Logon session to link them on |

### struct kacs_get_linked_token_args

Total size: **4 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `result_fd` | `s32` | Output: fd to the partner token |

### struct kacs_adjust_groups_args

Total size: **24 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `count` | `u32` | Number of `kacs_group_entry` elements (max 256) |
| 4 | 4 | `_pad` | `u32` | Reserved, must be 0 (alignment padding) |
| 8 | 8 | `data_ptr` | `u64` | Userspace pointer to `kacs_group_entry[]` array |
| 16 | 8 | `previous_state` | `u64` | Output: bitmask of previous enabled state (up to 64 groups) |

### struct kacs_group_entry

Total size: **8 bytes**. Array element pointed to by `kacs_adjust_groups_args.data_ptr`.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `index` | `u32` | Group index (`0xFFFFFFFF` in first entry = reset all groups) |
| 4 | 4 | `enable` | `u32` | 1 = enable, 0 = disable |

### struct kacs_adjust_default_args

Total size: **16 bytes**.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 8 | `dacl_ptr` | `u64` | Userspace pointer to binary ACL. Three-way encoding: `dacl_ptr=0, dacl_len=0` → no change; `dacl_ptr!=0, dacl_len>0` → replace DACL; `dacl_ptr!=0, dacl_len=0` → clear DACL (set to null). |
| 8 | 4 | `dacl_len` | `u32` | ACL length in bytes (max 65536). See dacl_ptr for semantics. |
| 12 | 2 | `owner_index` | `u16` | New owner SID index (`0xFFFF` = don't change) |
| 14 | 2 | `group_index` | `u16` | New primary group index (`0xFFFF` = don't change) |

### struct kacs_open_how

Total size: **32 bytes**. Passed by pointer to syscall 1020 (`kacs_open`).

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `desired_access` | `__u32` | KACS access mask (FILE_READ_DATA, etc.) |
| 4 | 4 | `create_disposition` | `__u32` | `KACS_FILE_*` constant (0-5) |
| 8 | 4 | `create_options` | `__u32` | Create options flags |
| 12 | 4 | `flags` | `__u32` | `AT_SYMLINK_NOFOLLOW` etc. |
| 16 | 8 | `sd_ptr` | `__aligned_u64` | Userspace pointer to creator SD (0 = inherit from parent) |
| 24 | 4 | `sd_len` | `__u32` | Length of creator SD |
| 28 | 4 | `__pad` | `__u32` | Reserved, must be 0 |

### struct kacs_node_result

Total size: **8 bytes**. Output array element for syscall 1024 (`kacs_access_check_list`).

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `granted` | `u32` | Access mask granted for this node |
| 4 | 4 | `status` | `s32` | 0 = granted, -EACCES = denied |

### struct kacs_object_type_entry

Total size: **20 bytes**. Input array element referenced by
`kacs_access_check_args.object_tree_ptr`.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 2 | `level` | `u16` | Tree depth. Root MUST be 0. Children appear immediately after their parent subtree in preorder. |
| 2 | 2 | `_reserved` | `u16` | Reserved, must be 0. |
| 4 | 16 | `guid` | `u8[16]` | Node GUID. Uses the same 16-byte binary GUID form as object ACE `ObjectType` fields. |

`object_tree_ptr` points to a flat preorder array of `struct kacs_object_type_entry`
values, `object_tree_count` entries long. The semantic validation rules are the
same as the Object ACEs section:

- the array MUST NOT be empty when provided
- the first entry MUST have `level = 0`
- there MUST be exactly one level-0 entry
- level gaps MUST be rejected
- duplicate GUIDs MUST be rejected
- every `_reserved` field MUST be 0

This ABI carries only the information the evaluator consumes: tree depth and
GUID identity. Parentage is derived from preorder depth transitions.

## 5. Token Wire Format (kacs_create_token spec)

Binary layout passed to syscall 1003 (`kacs_create_token`). Fixed 192-byte header followed by variable-length sections. Offsets in the header point to the variable sections. All offset/length pairs: offset=0 AND length=0 means absent/none.

**Wire format version:** `TOKEN_SPEC_VERSION = 2`

**Minimum size:** 192 bytes (header only). Maximum size: 65536 bytes.

### Header (192 bytes)

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `version` | `u32` | Must be `2` (`TOKEN_SPEC_VERSION`) |
| 4 | 1 | `token_type` | `u8` | 1 = Primary, 2 = Impersonation |
| 5 | 1 | `impersonation_level` | `u8` | 0 = Anonymous, 1 = Identification, 2 = Impersonation, 3 = Delegation |
| 6 | 2 | `_reserved0` | `u8[2]` | Must be 0 |
| 8 | 4 | `integrity_rid` | `u32` | Integrity level RID: 0=Untrusted, 4096=Low, 8192=Medium, 12288=High, 16384=System |
| 12 | 4 | `mandatory_policy` | `u32` | NO_WRITE_UP=0x01, NEW_PROCESS_MIN=0x02 |
| 16 | 8 | `privs_present` | `u64` | Bitmask of privileges present |
| 24 | 8 | `privs_enabled` | `u64` | Bitmask of privileges initially enabled. The kernel initializes `enabled_by_default` to this same value — no separate wire field. AdjustPrivileges reset-to-defaults restores `enabled` to this value. |
| 32 | 4 | `_reserved1` | `u32` | Must be 0 (elevation_type set only by LINK_TOKENS) |
| 36 | 4 | `projected_uid` | `u32` | Linux UID for credential projection |
| 40 | 4 | `projected_gid` | `u32` | Linux GID for credential projection |
| 44 | 4 | `audit_policy` | `u32` | Per-token audit flags (OBJECT_ACCESS_SUCCESS=0x01, etc.) |
| 48 | 8 | `expiration` | `u64` | Expiration timestamp. 0 = no expiry. |
| 56 | 8 | `session_id` | `u64` | Logon session ID (used as auth_id) |
| 64 | 4 | `owner_sid_index` | `u32` | Owner SID index: 0=user SID, 1..N=group |
| 68 | 4 | `primary_group_index` | `u32` | Primary group SID index: 0=user SID, 1..N=group |
| 72 | 8 | `source_name` | `u8[8]` | Token source name (e.g. `"authd\0\0\0"`) |
| 80 | 8 | `source_id` | `u64` | Token source identifier (LUID) |
| 88 | 4 | `user_sid_offset` | `u32` | Byte offset to user SID |
| 92 | 4 | `groups_offset` | `u32` | Byte offset to groups array |
| 96 | 4 | `groups_count` | `u32` | Number of group entries in the groups array |
| 100 | 4 | `default_dacl_offset` | `u32` | Byte offset to default DACL (0=none) |
| 104 | 4 | `default_dacl_len` | `u32` | Default DACL length (0=none) |
| 108 | 4 | `user_claims_offset` | `u32` | Byte offset to user claims array (0=none) |
| 112 | 4 | `user_claims_len` | `u32` | User claims total byte length (0=none) |
| 116 | 4 | `device_claims_offset` | `u32` | Byte offset to device claims array (0=none) |
| 120 | 4 | `device_claims_len` | `u32` | Device claims total byte length (0=none) |
| 124 | 4 | `device_groups_offset` | `u32` | Byte offset to device groups array (0=none) |
| 128 | 4 | `device_groups_count` | `u32` | Number of device group entries (0=none) |
| 132 | 4 | `restricted_sids_offset` | `u32` | Byte offset to restricted SIDs array (0=none) |
| 136 | 4 | `restricted_sids_count` | `u32` | Number of restricted SID entries (0=none) |
| 140 | 4 | `confinement_sid_offset` | `u32` | Byte offset to confinement SID (0=none) |
| 144 | 4 | `confinement_sid_len` | `u32` | Confinement SID length (0=none) |
| 148 | 4 | `confinement_caps_offset` | `u32` | Byte offset to confinement capabilities array (0=none) |
| 152 | 4 | `confinement_caps_count` | `u32` | Number of confinement capability entries (0=none) |
| 156 | 1 | `confinement_exempt` | `u8` | 1=exempt from confinement, 0=normal |
| 157 | 1 | `write_restricted` | `u8` | 1=write-restricted mode, 0=normal |
| 158 | 1 | `user_deny_only` | `u8` | 1=user SID matches deny ACEs only, 0=normal |
| 159 | 1 | `isolation_boundary` | `u8` | 1=enable namespace filtering (not enforced in v0.20), 0=normal |
| 160 | 4 | `supp_gids_offset` | `u32` | Byte offset to projected supplementary GIDs array (0=none) |
| 164 | 4 | `supp_gids_count` | `u32` | Number of supplementary GID entries (0=none) |
| 168 | 4 | `restricted_device_groups_offset` | `u32` | Byte offset to restricted device groups (0=none) |
| 172 | 4 | `restricted_device_groups_count` | `u32` | Number of restricted device group entries (0=none) |
| 176 | 8 | `origin` | `u64` | Originating logon session LUID (0 for non-derived tokens) |
| 184 | 4 | `interactive_session_id` | `u32` | Interactive session number (0 for services) |
| 188 | 4 | `_reserved3` | `u32` | Must be 0 |

### Variable sections

All variable sections are located at their header-specified offsets. Sections may appear in any order. The kernel validates that all offsets + lengths fall within the spec buffer.

#### User SID

At `user_sid_offset`. Binary SID: `[revision:u8][sub_count:u8][authority:u8[6]][sub_authorities:u32le[sub_count]]`.

#### Groups array

At `groups_offset`. Repeated `groups_count` times. Each entry:

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `sid_len` | `u32` | Length of the following SID in bytes |
| 4 | var | `sid` | `u8[sid_len]` | Binary SID |
| 4+sid_len | 4 | `attributes` | `u32` | Group attributes (SE_GROUP_* flags) |

The kernel derives the logon SID from `session_id` (`S-1-5-5-{session_id >> 32}-{session_id & 0xFFFFFFFF}`) and appends it to the groups array with `SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED | SE_GROUP_LOGON_ID`. Callers MUST NOT include the logon SID in the supplied groups. `owner_sid_index` and `primary_group_index` are interpreted relative to the caller-supplied groups only (0 = user SID, 1..N = caller's groups[0..N-1]), not including the injected logon SID.

#### Default DACL (optional)

At `default_dacl_offset` with length `default_dacl_len`. Binary ACL format.

#### User claims / Device claims (optional)

At their respective offsets. Each is a KACS claim array:

```
repeat until buffer exhausted:
  [entry_len:u32le]
  [entry_bytes: entry_len bytes]
```

where `entry_bytes` is one claim entry using the Claim Attribute Format
section. Total byte length is given by the `_len` field.

#### Device groups / Restricted SIDs / Confinement capabilities / Restricted device groups (optional)

Same format as the groups array (sid_len + sid + attributes per entry). Count given by the `_count` field.

#### Confinement SID (optional)

At `confinement_sid_offset`. Single binary SID. Length given by `confinement_sid_len`.

#### Projected supplementary GIDs (optional)

At `supp_gids_offset`. Array of `u32le` GID values, `supp_gids_count` entries.

## 6. Session Wire Format (kacs_create_session spec)

Binary layout passed to syscall 1004 (`kacs_create_session`). Minimum size: 15 bytes (1 + 2 + 0 + 4 + 8 = empty auth_package + minimum SID). Maximum size: 4096 bytes.

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 1 | `logon_type` | `u8` | Logon type value (see table below) |
| 1 | 2 | `auth_pkg_len` | `u16` | Length of auth package name |
| 3 | var | `auth_pkg` | `u8[auth_pkg_len]` | Authentication package name (e.g. `"Negotiate"`, `"Kerberos"`) |
| 3+auth_pkg_len | 4 | `user_sid_len` | `u32` | Length of user SID |
| 7+auth_pkg_len | var | `user_sid` | `u8[user_sid_len]` | Binary SID of the authenticated user |

### Logon types

| Type | Value | Meaning |
|------|-------|---------|
| Interactive | `2` | Console or GUI login |
| Network | `3` | Network authentication (SMB, HTTP, etc.) |
| Batch | `4` | Batch job (scheduled task) |
| Service | `5` | System service |
| NetworkCleartext | `8` | Network cleartext (FTP, HTTP Basic) |
| NewCredentials | `9` | New credentials (runas-style) |

### Logon SID derivation

The kernel assigns a session ID (u64) and derives the logon SID as: `S-1-5-5-{session_id >> 32}-{session_id & 0xFFFFFFFF}`.

## 7. Forward Compatibility Rules

### kacs_access_check_args versioning

The `size` field at offset 0 of `struct kacs_access_check_args` enables forward-compatible extension. The kernel copies `min(usize, sizeof(struct kacs_access_check_args))` bytes from userspace. Fields beyond the caller's struct size are zero-initialized. The minimum accepted size is `KACS_ACCESS_CHECK_ARGS_V1_SIZE = 40` bytes (through `generic_all`).

New fields are appended to the end of the struct. Older userspace that passes a smaller `size` gets zero-filled defaults for new fields. Newer userspace on an older kernel simply has trailing fields ignored.

### kacs_open howsize versioning

Syscall 1020 (`kacs_open`) takes a `howsize` parameter specifying the size of the caller's `struct kacs_open_how`. The kernel uses the same copy-min pattern as `kacs_access_check_args`: it copies `min(howsize, sizeof(struct kacs_open_how))` bytes from userspace, zero-initializing any fields the caller did not provide. The minimum accepted `howsize` is 16 bytes (through `flags`). If the caller provides a larger struct than the kernel knows about, trailing bytes beyond the kernel's struct size MUST all be zero — otherwise `-EINVAL` is returned (preventing old kernels from silently ignoring new flags).

## 8. Process Access Rights

Object-specific access rights for process objects (bits 0-15). Used in process SD DACLs and AccessCheck calls for `kacs_open_process_token`, `ptrace`, signals, etc.

| Constant | Value | Bit | Description |
|----------|-------|-----|-------------|
| `PROCESS_TERMINATE` | `0x0001` | 0 | Terminate the process (SIGKILL, SIGTERM, etc.) |
| `PROCESS_SIGNAL` | `0x0002` | 1 | Send non-lethal signals |
| `PROCESS_VM_READ` | `0x0010` | 4 | Read virtual memory (PTRACE_MODE_READ) |
| `PROCESS_VM_WRITE` | `0x0020` | 5 | Write virtual memory (PTRACE_MODE_ATTACH) |
| `PROCESS_DUP_HANDLE` | `0x0040` | 6 | Duplicate handles (pidfd_getfd) |
| `PROCESS_SET_INFORMATION` | `0x0200` | 9 | Set process attributes (prctl, etc.) |
| `PROCESS_SUSPEND_RESUME` | `0x0800` | 11 | Send stop/continue signals (SIGSTOP, SIGTSTP, SIGCONT, etc.) |
| `PROCESS_QUERY_INFORMATION` | `0x0400` | 10 | Query process information, open process token |
| `PROCESS_QUERY_LIMITED` | `0x1000` | 12 | Query limited information (pidfd_open) |

## 9. File/Directory Access Rights

Object-specific access rights for file and directory objects (bits 0-8). Used in file/directory SD DACLs and the `desired_access` field of `kacs_open_how`.

### File rights

| Constant | Value | Bit | Description |
|----------|-------|-----|-------------|
| `FILE_READ_DATA` | `0x0001` | 0 | Read file data |
| `FILE_WRITE_DATA` | `0x0002` | 1 | Write file data |
| `FILE_APPEND_DATA` | `0x0004` | 2 | Append data |
| `FILE_READ_EA` | `0x0008` | 3 | Read extended attributes |
| `FILE_WRITE_EA` | `0x0010` | 4 | Write extended attributes |
| `FILE_EXECUTE` | `0x0020` | 5 | Execute file |
| `FILE_DELETE_CHILD` | `0x0040` | 6 | (Directory only) Delete child entries |
| `FILE_READ_ATTRIBUTES` | `0x0080` | 7 | Read file attributes |
| `FILE_WRITE_ATTRIBUTES` | `0x0100` | 8 | Write file attributes |

### Directory aliases

These constants occupy the same bit positions but carry directory-specific semantics:

| Constant | Value | Alias for |
|----------|-------|-----------|
| `FILE_LIST_DIRECTORY` | `0x0001` | `FILE_READ_DATA` |
| `FILE_ADD_FILE` | `0x0002` | `FILE_WRITE_DATA` |
| `FILE_ADD_SUBDIRECTORY` | `0x0004` | `FILE_APPEND_DATA` |
| `FILE_TRAVERSE` | `0x0020` | `FILE_EXECUTE` |

### Standard rights (common to all object types)

| Constant | Value | Bit | Description |
|----------|-------|-----|-------------|
| `DELETE` | `0x00010000` | 16 | Delete the object |
| `READ_CONTROL` | `0x00020000` | 17 | Read the security descriptor |
| `WRITE_DAC` | `0x00040000` | 18 | Modify the DACL |
| `WRITE_OWNER` | `0x00080000` | 19 | Change the owner SID |
| `SYNCHRONIZE` | `0x00100000` | 20 | Synchronize on the object |
| `ACCESS_SYSTEM_SECURITY` | `0x01000000` | 24 | Read/write SACL (requires SeSecurityPrivilege) |
| `MAXIMUM_ALLOWED` | `0x02000000` | 25 | Query mode: compute maximum grantable mask |

### Generic rights (mapped per object type)

| Constant | Value | Bit |
|----------|-------|-----|
| `GENERIC_ALL` | `0x10000000` | 28 |
| `GENERIC_EXECUTE` | `0x20000000` | 29 |
| `GENERIC_WRITE` | `0x40000000` | 30 |
| `GENERIC_READ` | `0x80000000` | 31 |

## 10. Token Access Rights

Per-handle access rights on a KACS token fd. Specified as the `access_mask` parameter to `kacs_open_self_token`, `kacs_open_process_token`, etc. and checked on each ioctl.

| Constant | Value | Bit | Description |
|----------|-------|-----|-------------|
| `KACS_TOKEN_ASSIGN_PRIMARY` | `0x0001` | 0 | Install as process primary token (IOC_INSTALL) |
| `KACS_TOKEN_DUPLICATE` | `0x0002` | 1 | Duplicate the token (IOC_DUPLICATE, IOC_RESTRICT) |
| `KACS_TOKEN_IMPERSONATE` | `0x0004` | 2 | Impersonate the token (IOC_IMPERSONATE) |
| `KACS_TOKEN_QUERY` | `0x0008` | 3 | Query token attributes (IOC_QUERY, IOC_GET_LINKED_TOKEN) |
| `KACS_TOKEN_ADJUST_PRIVS` | `0x0020` | 5 | Adjust privileges (IOC_ADJUST_PRIVS) |
| `KACS_TOKEN_ADJUST_GROUPS` | `0x0040` | 6 | Adjust groups (IOC_ADJUST_GROUPS) |
| `KACS_TOKEN_ADJUST_DEFAULT` | `0x0080` | 7 | Adjust default DACL/owner/group (IOC_ADJUST_DEFAULT) |
| `KACS_TOKEN_ADJUST_SESSIONID` | `0x0100` | 8 | Adjust interactive session ID (IOC_ADJUST_SESSIONID) |
| `KACS_TOKEN_ALL_ACCESS` | `0x000F01FF` | 0-8, 16-19 | All token-specific rights (0x01FF, including reserved bit 4 = 0x0010 for TOKEN_QUERY_SOURCE) + STANDARD_RIGHTS_REQUIRED (DELETE \| READ_CONTROL \| WRITE_DAC \| WRITE_OWNER = 0x000F0000) |

## 11. IPC Access Rights

Object-specific access rights for SysV IPC objects (shared memory segments, semaphore arrays, message queues). Used in IPC object SD DACLs.

| Constant | Value | Bit | Description |
|----------|-------|-----|-------------|
| `IPC_READ_DATA` | `0x0001` | 0 | Read object data (shmat read, semctl GETVAL/GETALL, msgrcv) |
| `IPC_WRITE_DATA` | `0x0002` | 1 | Write/modify object data (shmat write, semop alter, semctl SETVAL/SETALL, msgsnd) |
| `IPC_READ_ATTRIBUTES` | `0x0004` | 2 | Query object attributes (IPC_STAT, GETPID/GETNCNT/GETZCNT) |
| `IPC_WRITE_ATTRIBUTES` | `0x0008` | 3 | Modify object attributes (IPC_SET) |

### IPC GenericMapping

| Generic right | Maps to |
|---|---|
| GENERIC_READ | IPC_READ_DATA \| IPC_READ_ATTRIBUTES \| READ_CONTROL \| SYNCHRONIZE |
| GENERIC_WRITE | IPC_WRITE_DATA \| IPC_WRITE_ATTRIBUTES \| WRITE_DAC \| SYNCHRONIZE |
| GENERIC_EXECUTE | IPC_READ_ATTRIBUTES \| READ_CONTROL \| SYNCHRONIZE |
| GENERIC_ALL | IPC_READ_DATA \| IPC_WRITE_DATA \| IPC_READ_ATTRIBUTES \| IPC_WRITE_ATTRIBUTES \| DELETE \| READ_CONTROL \| WRITE_DAC \| WRITE_OWNER \| SYNCHRONIZE |

### Privilege attribute constants (for kacs_priv_entry)

| Constant | Value |
|----------|-------|
| `SE_PRIVILEGE_ENABLED` | `0x00000002` |
| `SE_PRIVILEGE_REMOVED` | `0x00000004` |

### Group attribute constants (for SID_AND_ATTRIBUTES in query results)

| Constant | Value | Description |
|----------|-------|-------------|
| `SE_GROUP_MANDATORY` | `0x00000001` | Cannot be disabled via AdjustGroups |
| `SE_GROUP_ENABLED_BY_DEFAULT` | `0x00000002` | Enabled at creation time |
| `SE_GROUP_ENABLED` | `0x00000004` | Currently enabled for access checking |
| `SE_GROUP_OWNER` | `0x00000008` | Can be set as default owner for new objects |
| `SE_GROUP_USE_FOR_DENY_ONLY` | `0x00000010` | Matches deny ACEs only, not allow ACEs |
| `SE_GROUP_INTEGRITY` | `0x00000020` | Identifies an integrity level SID |
| `SE_GROUP_INTEGRITY_ENABLED` | `0x00000040` | Used with SE_GROUP_INTEGRITY |
| `SE_GROUP_RESOURCE` | `0x20000000` | Domain-local group from resource domain |
| `SE_GROUP_LOGON_ID` | `0xC0000000` | Identifies the per-session logon SID |

### Logon type values (for session wire format and TOKEN_CLASS_LOGON_TYPE)

| Type | Value |
|------|-------|
| Interactive | `2` |
| Network | `3` |
| Batch | `4` |
| Service | `5` |
| NetworkCleartext | `8` |
| NewCredentials | `9` |

### Logon SID derivation

The logon SID is derived from the session ID (a u64 LUID):

```
S-1-5-5-{session_id >> 32}-{session_id & 0xFFFFFFFF}
```

Authority = 5 (NT Authority), first sub-authority = 5 (Logon SID prefix), second sub-authority = high 32 bits of session ID, third sub-authority = low 32 bits.

### SID binary format endianness note

SIDs use mixed endianness per MS-DTYP: the 6-byte `IdentifierAuthority` field is **big-endian**, while the `SubAuthority[]` array entries are **little-endian** u32 values. This is an exception to the global little-endian rule stated at the top of this document.

### kacs_open_how create options

| Constant | Value | Description |
|----------|-------|-------------|
| `KACS_CREATE_OPT_DIRECTORY` | `0x0001` | The target must be a directory |
| `KACS_CREATE_OPT_DELETE_ON_CLOSE` | `0x0002` | Delete the file when the last handle is closed |

### kacs_get_sd / kacs_set_sd flags

The `flags` parameter accepts standard Linux `AT_*` flags:

| Flag | Value | Description |
|------|-------|-------------|
| `AT_EMPTY_PATH` | `0x1000` | Operate on the fd itself (not a path relative to it) |
| `AT_SYMLINK_NOFOLLOW` | `0x100` | Do not follow symlinks |

### kacs_open status_out values

Written to the `status_out` pointer (if non-NULL) after `kacs_open` completes:

| Status | Value | Description |
|--------|-------|-------------|
| `KACS_STATUS_OPENED` | `1` | Existing file was opened |
| `KACS_STATUS_CREATED` | `2` | New file was created |
| `KACS_STATUS_OVERWRITTEN` | `3` | Existing file was truncated to zero |
| `KACS_STATUS_SUPERSEDED` | `4` | Existing file was deleted and recreated |

### Empty query results

When a query class returns an optional value that is absent:
- **Optional SID** (e.g., TOKEN_CLASS_APPCONTAINER_SID when not confined): zero bytes returned (`buf_len` output = 0).
- **Optional ACL** (e.g., TOKEN_CLASS_DEFAULT_DACL when no default DACL): zero bytes returned.
- **Optional SID array** (e.g., TOKEN_CLASS_RESTRICTED_SIDS when unrestricted): `[count:u32le = 0]` (4 bytes).

### Privilege bit positions (LUID values)

Each privilege is a bit position in a u64 bitmask. Standard Windows-compatible positions (bits 2-35), Peios custom (bits 62-63).

| Privilege | Bit | Bitmask |
|-----------|-----|---------|
| SeCreateTokenPrivilege | 2 | `0x0000000000000004` |
| SeAssignPrimaryTokenPrivilege | 3 | `0x0000000000000008` |
| SeLockMemoryPrivilege | 4 | `0x0000000000000010` |
| SeIncreaseQuotaPrivilege | 5 | `0x0000000000000020` |
| SeMachineAccountPrivilege | 6 | `0x0000000000000040` |
| SeTcbPrivilege | 7 | `0x0000000000000080` |
| SeSecurityPrivilege | 8 | `0x0000000000000100` |
| SeTakeOwnershipPrivilege | 9 | `0x0000000000000200` |
| SeLoadDriverPrivilege | 10 | `0x0000000000000400` |
| SeSystemProfilePrivilege | 11 | `0x0000000000000800` |
| SeSystemtimePrivilege | 12 | `0x0000000000001000` |
| SeProfileSingleProcessPrivilege | 13 | `0x0000000000002000` |
| SeIncreaseBasePriorityPrivilege | 14 | `0x0000000000004000` |
| SeCreatePagefilePrivilege | 15 | `0x0000000000008000` |
| SeCreatePermanentPrivilege | 16 | `0x0000000000010000` |
| SeBackupPrivilege | 17 | `0x0000000000020000` |
| SeRestorePrivilege | 18 | `0x0000000000040000` |
| SeShutdownPrivilege | 19 | `0x0000000000080000` |
| SeDebugPrivilege | 20 | `0x0000000000100000` |
| SeAuditPrivilege | 21 | `0x0000000000200000` |
| SeSystemEnvironmentPrivilege | 22 | `0x0000000000400000` |
| SeChangeNotifyPrivilege | 23 | `0x0000000000800000` |
| SeRemoteShutdownPrivilege | 24 | `0x0000000001000000` |
| SeUndockPrivilege | 25 | `0x0000000002000000` |
| SeSyncAgentPrivilege | 26 | `0x0000000004000000` |
| SeEnableDelegationPrivilege | 27 | `0x0000000008000000` |
| SeManageVolumePrivilege | 28 | `0x0000000010000000` |
| SeImpersonatePrivilege | 29 | `0x0000000020000000` |
| SeCreateGlobalPrivilege | 30 | `0x0000000040000000` |
| SeTrustedCredManAccessPrivilege | 31 | `0x0000000080000000` |
| SeRelabelPrivilege | 32 | `0x0000000100000000` |
| SeIncreaseWorkingSetPrivilege | 33 | `0x0000000200000000` |
| SeTimeZonePrivilege | 34 | `0x0000000400000000` |
| SeCreateSymbolicLinkPrivilege | 35 | `0x0000000800000000` |
| SeCreateJobPrivilege (Peios) | 62 | `0x4000000000000000` |
| SeBindPrivilegedPortPrivilege (Peios) | 63 | `0x8000000000000000` |

### Token GenericMapping

Used when AccessCheck evaluates a token's own SD (e.g., when opening a token fd):

| Field | Value |
|-------|-------|
| `read` | `TOKEN_QUERY \| READ_CONTROL` = `0x00020008` |
| `write` | `TOKEN_ADJUST_PRIVILEGES \| TOKEN_ADJUST_GROUPS \| TOKEN_ADJUST_DEFAULT \| WRITE_DAC` = `0x000400E0` |
| `execute` | `TOKEN_IMPERSONATE` = `0x00000004` |
| `all` | `TOKEN_ALL_ACCESS` = `0x000F01FF` |

### kacs_access_check_list: results_count

`results_count` MUST equal the number of nodes in the `object_tree_ptr` array passed in `kacs_access_check_args`. If they differ, the syscall returns `-EINVAL`.

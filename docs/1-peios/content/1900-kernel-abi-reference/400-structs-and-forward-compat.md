---
title: Structs and forward-compat
type: reference
description: Struct layouts for the parameter records that KACS syscalls and ioctls use, plus the size-versioning rules that make the ABI forward-compatible. This page catalogues every struct that crosses the kernel boundary and the minimum sizes the kernel accepts.
related:
  - peios/kernel-abi-reference/overview
  - peios/kernel-abi-reference/syscalls
  - peios/kernel-abi-reference/token-ioctls
  - peios/wire-formats-reference/overview
---

The KACS syscalls and ioctls pass parameter structs across the kernel boundary. Each struct has a fixed layout — field offsets, sizes, types. Some are **size-versioned**: the struct carries a size field at offset 0, and the kernel reads only up to whatever size the caller declares. This page catalogues the structs and the size-versioning rules.

For wire-format payloads (token wire format, session wire format, SD self-relative layout, conditional ACE bytecode, CAAP wire format), see [Wire formats reference](~peios/wire-formats-reference/overview). The structs here are syscall parameter records; the wire formats there are payloads pointed to by struct fields.

All numeric fields are **little-endian** on x86_64.

## Forward-compatibility model

Several structs are versioned by size at the wire level. The pattern:

1. The first field of the struct is the size (in bytes) the caller is using.
2. The kernel reads `min(declared_size, kernel_known_size)` bytes.
3. Fields beyond the kernel's known size must be zero (otherwise `-EINVAL`).
4. New struct versions append fields at the end. Older callers don't write the new fields; their `size` declares the smaller layout; the kernel uses defaults for the unknown fields.

This pattern lets userspace built for an older kernel work against a newer one (new fields default), and lets userspace built for a newer kernel fail gracefully on an older one (it would set fields beyond the old kernel's known size, which the old kernel doesn't accept unless they're zero).

Three structs use this pattern in v0.20:

| Struct | Field controlling version | Minimum size (v1) |
|---|---|---|
| `kacs_access_check_args` | `size` at offset 0 | 40 bytes (`KACS_ACCESS_CHECK_ARGS_V1_SIZE`) |
| `kacs_open_how` | `howsize` parameter (separate from struct) | 16 bytes (through `flags` field) |
| `kacs_mount_policy_args` | `argsize` parameter | 16 bytes |

The other structs documented here are fixed-size in v0.20. Future versions may convert them to the size-versioned pattern if extension is needed.

## kacs_access_check_args

Used by `kacs_access_check` and `kacs_access_check_list`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `size` | Size of this struct as known to the caller. |
| 4 | 4 | `token_fd` | The calling token. |
| 8 | 8 | `sd_ptr` | Userspace pointer to the SD blob. |
| 16 | 4 | `sd_len` | Length of the SD blob. |
| 20 | 4 | `desired_access` | Requested access mask. |
| 24 | 4 | `generic_read` | GenericMapping: READ → object-specific bits. |
| 28 | 4 | `generic_write` | GenericMapping: WRITE → object-specific bits. |
| 32 | 4 | `generic_execute` | GenericMapping: EXECUTE → object-specific bits. |
| 36 | 4 | `generic_all` | GenericMapping: ALL → object-specific bits. |
| 40 | 8 | `self_sid_ptr` | Pointer to `self_sid` (for `PRINCIPAL_SELF` ACE resolution); may be NULL. |
| 48 | 4 | `self_sid_len` | Length of self_sid in bytes; 0 if NULL. |
| 52 | 4 | `privilege_intent` | Flags: `BACKUP_INTENT` (0x01), `RESTORE_INTENT` (0x02). |
| 56 | 8 | `object_tree_ptr` | For `kacs_access_check_list`: pointer to flat array of `kacs_object_type_entry`. NULL for simple check. |
| 64 | 4 | `object_tree_count` | Number of entries in object_tree. |
| 68 | 4 | `pip_type` | The calling process's PSB pip_type (caller supplies; kernel doesn't read it itself). |
| 72 | 4 | `pip_trust` | Calling process's pip_trust. |
| 76 | 4 | _pad | Reserved; must be zero. |
| 80 | 8 | `local_claims_ptr` | Pointer to local-claims buffer (multi-entry KACS claim format). NULL if no `@Local` claims. |
| 88 | 4 | `local_claims_len` | Length. |
| 92 | 4 | `granted_out` | Output: the granted access mask. |
| 96 | 8 | `granted_out_ptr` | (For per-node variant) Reserved; pass NULL for single-result calls. |
| 104 | 8 | `audit_context_ptr` | Pointer to caller-supplied opaque object identifier for audit events. May be NULL. |
| 112 | 4 | `audit_context_len` | Length. |
| 116 | 4 | `continuous_audit_out` | Output: the continuous-audit mask to cache on the handle. |
| 120 | 8 | `continuous_audit_out_ptr` | (Reserved) |
| 128 | 4 | `staging_mismatch_out` | Output: 1 if any CAAP staging mismatch occurred, 0 otherwise. |
| 132 | 4 | _pad | Reserved. |

Total v1 size: **136 bytes**. Minimum size the kernel accepts: **40 bytes** (`KACS_ACCESS_CHECK_ARGS_V1_SIZE`). Callers using the minimum size pass NULL for the optional pointer fields and zero for the output fields.

## kacs_open_how

Used by `kacs_open`. The `howsize` parameter to the syscall controls how much of this struct the kernel reads.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `desired_access` | Requested access mask. |
| 4 | 4 | `create_disposition` | `KACS_FILE_*` constant (0–5). |
| 8 | 4 | `create_options` | Flags: `KACS_CREATE_OPT_DIRECTORY` (0x01), `KACS_CREATE_OPT_DELETE_ON_CLOSE` (0x02). |
| 12 | 4 | `flags` | Path flags: `AT_EMPTY_PATH` (0x1000), `AT_SYMLINK_NOFOLLOW` (0x100). |
| 16 | 8 | `sd_ptr` | Creator-supplied SD for new files. NULL to inherit from parent. |
| 24 | 4 | `sd_len` | Length of SD blob. |
| 28 | 4 | _pad | Reserved; must be zero. |

Total v1 size: **32 bytes**. Minimum `howsize` the kernel accepts: **16 bytes** (through the `flags` field). Callers using the minimum cannot supply a creator SD.

## kacs_mount_policy_args

Used by `kacs_get_mount_policy` and `kacs_set_mount_policy`. The `argsize` parameter controls how much is read.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `policy` | The policy class constant (`KACS_MOUNT_POLICY_*`). |
| 4 | 4 | `flags` | Reserved; must be zero. |
| 8 | 8 | `generation` | Output: current generation counter. |
| 16 | 8 | `template_sd_ptr` | Pointer to mount template SD. NULL for none. |
| 24 | 4 | `template_sd_len` | Length of template. 0 with NULL means no template. |
| 28 | 4 | _pad | Reserved. |

Total v1 size: **32 bytes**. Minimum `argsize`: **16 bytes**. Callers using the minimum cannot read or set the template.

## kacs_query_args

Used by `KACS_IOC_QUERY`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `token_class` | Numeric query class (1–24). |
| 4 | 4 | `buf_len` | Input: buffer size. Output: required size. |
| 8 | 8 | `buf_ptr` | Userspace pointer to output buffer. May be 0 for probe. |

Total: **16 bytes**. Fixed-size.

## kacs_adjust_privs_args

Used by `KACS_IOC_ADJUST_PRIVS`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `count` | Number of `kacs_priv_entry` records. |
| 4 | 4 | _pad | Reserved. |
| 8 | 8 | `data_ptr` | Pointer to array of `kacs_priv_entry`. |
| 16 | 8 | `previous_enabled` | Output: previous `enabled` bitmask. |

Total: **24 bytes**.

### kacs_priv_entry

Array element (each entry is 8 bytes):

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `luid` | Privilege LUID (bit position 0–63). 0 with `KACS_PRIV_RESET_ALL_DEFAULTS` attributes is the reset sentinel. |
| 4 | 4 | `attributes` | 0 (disable), `SE_PRIVILEGE_ENABLED` (0x02 = enable), `SE_PRIVILEGE_REMOVED` (0x04 = remove), `KACS_PRIV_RESET_ALL_DEFAULTS` (0x80000000 = reset). |

## kacs_adjust_groups_args

Used by `KACS_IOC_ADJUST_GROUPS`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `count` | Number of `kacs_group_entry` records. |
| 4 | 4 | _pad | Reserved. |
| 8 | 8 | `data_ptr` | Pointer to array. |
| 16 | 8 | `previous_state` | Output: previous enabled state bitmask. |

Total: **24 bytes**.

### kacs_group_entry

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `index` | 0-based index into the token's groups array. `0xFFFFFFFF` is the reset-all sentinel. |
| 4 | 4 | `enable` | 1 to enable, 0 to disable. |

8 bytes per entry.

## kacs_adjust_default_args

Used by `KACS_IOC_ADJUST_DEFAULT`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 8 | `dacl_ptr` | Three-way: 0 = no change; nonzero with len>0 = replace; nonzero with len=0 = clear. |
| 8 | 4 | `dacl_len` | DACL length. |
| 12 | 2 | `owner_index` | `0xFFFF` = no change; otherwise the new owner-SID index. |
| 14 | 2 | `group_index` | Same for primary group. |

Total: **16 bytes**.

## kacs_duplicate_args

Used by `KACS_IOC_DUPLICATE`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `access_mask` | Desired access mask for the new fd. |
| 4 | 4 | `token_type` | 1 = Primary, 2 = Impersonation. |
| 8 | 4 | `impersonation_level` | 0–3. |
| 12 | 4 | `result_fd` | Output: the new fd. |

Total: **16 bytes**.

## kacs_restrict_args

Used by `KACS_IOC_RESTRICT`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 8 | `privs_to_delete` | Bitmask of privileges to remove. |
| 8 | 4 | `num_deny_indices` | Count of group indices to mark deny-only. |
| 12 | 4 | `num_restrict_sids` | Count of restricting SIDs to add. |
| 16 | 4 | `data_len` | Total length of the data payload. |
| 20 | 4 | `flags` | `KACS_RESTRICT_WRITE_RESTRICTED` (0x01). |
| 24 | 8 | `data_ptr` | Pointer to payload: u32[] deny indices followed by packed binary SIDs. |
| 32 | 4 | `result_fd` | Output: the new fd. |
| 36 | 4 | _pad | Reserved. |

Total: **40 bytes**.

## kacs_link_tokens_args

Used by `KACS_IOC_LINK_TOKENS`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `elevated_fd` | Fd of the Full token. |
| 4 | 4 | `filtered_fd` | Fd of the Limited token. |
| 8 | 8 | `session_id` | Session LUID both tokens reference. |

Total: **16 bytes**.

## kacs_get_linked_token_args

Used by `KACS_IOC_GET_LINKED_TOKEN`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `result_fd` | Output: partner's fd. |

Total: **4 bytes**.

## kacs_node_result

Output array element for `kacs_access_check_list`.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 4 | `granted` | The granted mask for this node. |
| 4 | 4 | `status` | 0 = granted, `-EACCES` = denied. |

8 bytes per entry. Caller passes an array of these to receive per-node results.

## kacs_object_type_entry

Input array element for object type lists.

| Offset | Size | Field | Meaning |
|---|---|---|---|
| 0 | 2 | `level` | Tree depth (0 = root). |
| 2 | 2 | _reserved | Must be zero. |
| 4 | 16 | `guid` | Property GUID. |

20 bytes per entry. The array is a preorder flattening of the tree.

Validation: first entry's `level` must be 0; exactly one level-0 entry; no level gaps; no duplicate GUIDs; all `_reserved` zero.

## Forward-compat detail

For the three size-versioned structs (`kacs_access_check_args`, `kacs_open_how`, `kacs_mount_policy_args`), the rules in detail:

**When the caller declares a smaller size than the kernel knows**, the kernel reads up to the declared size. Fields the kernel "knows about" beyond the declared size get default values (zero, NULL, or a struct-specific default depending on the field).

**When the caller declares a larger size than the kernel knows**, the kernel:

1. Reads up to its own known size.
2. Reads (but does not interpret) the trailing bytes up to the declared size.
3. Checks that all trailing bytes are zero. If any non-zero byte is found beyond the kernel's known size, returns `-EINVAL`.

This is the "caller using new fields the kernel doesn't know" case. If the caller sets a new field (which would be zero on an older kernel), the older kernel sees non-zero trailing bytes and rejects the call. The userspace program can then notice the rejection and fall back to a compatible code path.

**When the caller declares a size smaller than the minimum** (e.g., less than 40 for `kacs_access_check_args`), the call is rejected with `-EINVAL`. The minimum is what the kernel needs to know to perform the operation at all.

The minimum sizes (`KACS_ACCESS_CHECK_ARGS_V1_SIZE` = 40; `kacs_open_how` minimum = 16; `kacs_mount_policy_args` minimum = 16) are stable; they will not change in future versions. Fields added after the v1 minimum are appended; the offsets of existing fields are stable.

---
title: LSM Blob Layouts
---

KACS registers blob sizes at LSM initialization. Each blob is allocated by the LSM framework and zeroed on allocation.

## Credential blob

Attached to `cred->security`. Contains a pointer to the token and pre-computed projected UIDs.

| Field | Description |
|---|---|
| `token` | Pointer to the refcounted token object. Immutable after `commit_creds()`. |
| `projected_uid` | Filesystem UID used by the `current_fsuid()` patch. Stamped from the token's `projected_uid` at credential creation. During impersonation, the impersonation credential carries the impersonated token's projected UID. |
| `projected_gid` | Filesystem GID used by the `current_fsgid()` patch. Same stamping rules as projected_uid. |

Within a process, multiple thread credentials share the same token (refcounted). At fork (`security_prepare_creds` without CLONE_THREAD), the child MUST receive an independent deep copy of the parent's token — mutations after fork are invisible across the process boundary. For thread creation (CLONE_THREAD), the token pointer is shared with refcount increment. `security_cred_free` decrements the refcount and frees the token when it reaches zero.

## File blob

Attached to `file->f_security`. The open-time authorization snapshot fields are
set once at open time and MUST NOT be modified afterward. Implementations MAY
store additional per-open-file-description lifecycle state in the same blob when
that state is not part of the authorization snapshot and cannot widen cached
granted rights.

| Field | Description |
|---|---|
| `granted` | Access rights granted at open time. Immutable. |
| `continuous_audit` | Continuous audit mask from SACL alarm ACEs. |
| `flags` | Authorization-snapshot flags including `KACS_FILE_FACS_MANAGED`. |
| `lifecycle_state` | Optional implementation-private lifecycle state for the open file description, such as delete-on-close lineage state. This state MAY change only under its specified lifecycle rules and MUST NOT modify `granted`, `continuous_audit`, or `KACS_FILE_FACS_MANAGED`. |

## Inode blob

Attached to `inode->i_security`. Contains the cached parsed-SD object.

| Field | Description |
|---|---|
| `sd_cache` | RCU-protected pointer to a cache object containing immutable validated self-relative SD bytes plus prevalidated component layout. Populated lazily on first access. Updated by `kacs_set_sd` via RCU replacement. Readers MAY pin the cache object by refcount before dropping the RCU read lock. Missing and ephemeral-synthetic cache entries record the superblock policy generation that produced them. Freed via `inode_free_security_rcu` after RCU grace and reader-pin draining. |

## Superblock blob

Attached to `super_block->s_security`. Contains FACS mount-adoption policy.

| Field | Description |
|---|---|
| `mount_policy` | One FACS mount-policy class. Initialized by the kernel classifier and mutable through `kacs_set_mount_policy` for managed classes only. |
| `policy_generation` | Monotonic counter incremented on every successful policy or template replacement. |
| `template_sd` | Optional complete self-relative file SD used as the mount-level synthesis template. |

## Task blob

Attached to `task_struct->security`. Contains the PSB fields and hook coordination state.

| Field | Description |
|---|---|
| `proc_sd` | Process security descriptor. |
| `pip_type` | PIP type (None, Protected, Isolated). |
| `pip_trust` | Trust level within PIP type. |
| `file_decision_inode` | Hook coordination: which inode was decided. |
| `file_decision_op` | Hook coordination: which operation class. |
| `kacs_open_desired` | KACS-native open: desired access for f_mode fixup. |
| `wxp`, `tlp`, `lsv` | Process mitigations. |
| `cfif`, `cfib` | Forward/backward-edge CFI. |
| `pie` | Reject non-PIE binaries. |
| `sml` | Speculation mitigation lock. |
| `ui_access` | UI interaction (reserved). |
| `no_child_process` | Fork restriction (one-way). |

## Socket blob

Attached to `sock->sk_security`. Used for IPC identity capture.

| Field | Description |
|---|---|
| `peer_token` | Server side accepted Unix stream/seqpacket socket: peer's token snapshot captured at `connect()`. NULL for datagram sockets, socketpair-created sockets, and sockets with no KACS connect-time capture. |
| `socket_sd` | Abstract sockets: SD set at `bind()` time. NULL for pathname sockets and socketpair. |
| `max_impersonation` | Client side: maximum impersonation level (default: Impersonation). |

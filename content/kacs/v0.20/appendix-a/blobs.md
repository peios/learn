---
title: LSM Blob Layouts
order: 3
---

KACS registers blob sizes at LSM initialization. Each blob is allocated by the LSM framework and zeroed on allocation.

## Credential blob

Attached to `cred->security`. Contains a pointer to the token and pre-computed projected UIDs.

| Field | Description |
|---|---|
| `token` | Pointer to the refcounted token object. Immutable after `commit_creds()`. |
| `projected_uid` | Filesystem UID used by the `current_fsuid()` patch. |
| `projected_gid` | Filesystem GID used by the `current_fsgid()` patch. |

Multiple credentials MAY share the same token (refcounted). `security_prepare_creds` copies the token pointer and increments the refcount. `security_cred_free` decrements it.

## File blob

Attached to `file->f_security`. Set once at open time, never modified.

| Field | Description |
|---|---|
| `granted` | Access rights granted at open time. Immutable. |
| `continuous_audit` | Continuous audit mask from SACL alarm ACEs. |
| `flags` | KACS_FILE_IOCTL_ONLY (mode-3 device open), KACS_FILE_FACS_MANAGED. |

## Inode blob

Attached to `inode->i_security`. Contains the cached parsed SD.

| Field | Description |
|---|---|
| `sd_cache` | RCU-protected pointer to the parsed SD. Populated lazily on first access. Updated by `kacs_set_sd` via RCU replacement. Freed via `inode_free_security_rcu`. |

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
| `peer_token` | Server side: peer's token snapshot captured at `connect()`. |
| `socket_sd` | Abstract sockets: SD set at `bind()` time. NULL for pathname sockets and socketpair. |
| `max_impersonation` | Client side: maximum impersonation level (default: Impersonation). |

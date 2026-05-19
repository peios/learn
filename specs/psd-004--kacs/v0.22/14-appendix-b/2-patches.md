---
title: Kernel Patches
---

KACS requires kernel patches beyond the LSM module itself. All patches are conditional on KACS being active and compile out when KACS is not configured.

## FACS handle-model patches

| # | Site | Purpose |
|---|---|---|
| 1 | `ksys_pwrite64()` | Classify effective append intent; deny positioned writes on append-only fd. |
| 2 | `ksys_pwritev()` / `pwritev2()` | Classify explicit offsets, `RWF_APPEND`, and `RWF_NOAPPEND`; deny positioned or no-append writes on append-only fd. |
| 3 | `io_write()` in io_uring | Classify SQE offsets, `RWF_APPEND`, and `RWF_NOAPPEND`; deny positioned or no-append writes on append-only fd. |
| 4 | `aio_write()` in fs/aio.c | Classify AIO offsets, `RWF_APPEND`, and `RWF_NOAPPEND`; deny positioned or no-append writes on append-only fd. |
| 5 | `do_faccessat()` | Skip credential swap to real_cred; use effective token. |
| 6 | `do_handle_open()` | Gate `open_by_handle_at()` behind SeChangeNotifyPrivilege. |
| 7 | `fchmod()` / `fchown()` / `futimens()` | New `security_file_setattr` hook with `struct file *`. |
| 8 | `vfs_fallocate()` | Deny mutation modes on append-only fd. |
| 9 | `vfs_fstat()` / `vfs_statx_fd()` | New `security_file_getattr` hook with `struct file *`. |
| 10 | `fgetxattr()` | New `security_file_getxattr` hook with `struct file *`. |
| 11 | `fsetxattr()` / `fremovexattr()` | New `security_file_setxattr` hook with `struct file *`. |

## Kernel interface and derooting patches

| # | Site | Purpose |
|---|---|---|
| 12 | KACS-native open handoff (`do_dentry_open()` or equivalent `security_file_open` handoff) | Carry KACS `desired_access` into the opened file, cache the granted mask, and set `f_mode` from the granted/requested data and execute rights before the fd is returned. |
| 13 | `pidfd_getfd()` | Add PTRACE_MODE_GETFD to distinguish fd extraction from ptrace attach. |
| 14 | `current_fsuid()` / `current_fsgid()` | Return projected UID/GID from KACS token instead of `cred->fsuid` / `cred->fsgid`. |
| 15 | `execveat` / `do_open_execat` | Not applied in v0.20. `execveat(AT_EMPTY_PATH)` uses live AccessCheck via re-opened file rather than checking the fd's granted mask. The granted-mask (snapshot) approach is the target for future versions. |
| 16 | `fchdir()` / `vfs_fchdir()` | Enforce FILE_TRAVERSE on directory fds. **Implementation note:** in v0.20, this is enforced via `security_file_permission` rather than a dedicated `security_file_fchdir` hook. Functionally equivalent. |
| 17 | `pidfd_open()` | Add `PTRACE_MODE_PIDFD_OPEN` so the LSM can distinguish process-handle acquisition from ptrace memory-read mode. |

## Hook coordination

Patches 7, 9, 10, and 11 add file-based hooks that fire while `struct file *` is available. The fd `file_getattr` / `file_setattr` patch points behave the same way. The subsequent dentry-based hook detects that the file hook already decided and becomes a no-op. Coordination uses a per-task marker:

| Field | Description |
|---|---|
| `inode` | Which object was decided. |
| `op_class` | SETATTR, GETATTR, FILEATTR_SET, FILEATTR_GET, SETXATTR, or GETXATTR. |

The marker is scoped to exactly one syscall invocation, one inode, one operation class. A matching dentry-based hook consumes and clears the marker. A mismatched dentry-based hook MUST clear the marker before continuing with normal authorization.

`FILEATTR_SET` has one VFS-specific exception: the same marker MAY authorize the immediate `inode_file_getattr` preflight for the same inode before it is consumed by `inode_file_setattr`. Any other inode or operation-class mismatch MUST clear the marker.

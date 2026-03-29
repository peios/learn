---
title: Kernel Patches
order: 2
---

KACS requires kernel patches beyond the LSM module itself. All patches are conditional on KACS being active and compile out when KACS is not configured.

## FACS handle-model patches

| # | Site | Purpose |
|---|---|---|
| 1 | `ksys_pwrite64()` | Deny positioned write on append-only fd. |
| 2 | `ksys_pwritev()` / `pwritev2()` | Deny positioned/vectored write + RWF_NOAPPEND on append-only fd. |
| 3 | `io_write()` in io_uring | Deny positioned write via io_uring on append-only fd. |
| 4 | `aio_write()` in fs/aio.c | Deny positioned write via AIO on append-only fd. |
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
| 12 | `do_dentry_open()` | Accept KACS desired_access, set f_mode from granted mask. |
| 13 | `pidfd_getfd()` | Add PTRACE_MODE_GETFD to distinguish fd extraction from ptrace attach. |
| 14 | `current_fsuid()` | Return projected UID from KACS token instead of `cred->fsuid`. |
| 15 | `execveat` / `do_open_execat` | Check FILE_EXECUTE on the original fd's granted mask. |
| 16 | `fchdir()` / `vfs_fchdir()` | New `security_file_fchdir` hook; check FILE_TRAVERSE in granted mask. |

## Hook coordination

Patches 7, 9, 10, and 11 add file-based hooks that fire while `struct file *` is available. The subsequent dentry-based hook detects that the file hook already decided and becomes a no-op. Coordination uses a per-task marker:

| Field | Description |
|---|---|
| `inode` | Which object was decided. |
| `op_class` | SETATTR, GETATTR, SETXATTR, or GETXATTR. |

The marker is scoped to exactly one syscall invocation, one inode, one operation class. It is cleared unconditionally at the end of each dentry-based hook.

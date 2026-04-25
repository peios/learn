---
title: LSM Hook Matrix
---

This is the definitive reference mapping file operations to LSM hooks and required access rights. Each entry specifies: enforcement mode (snapshot = granted mask check, live = AccessCheck against SD), the hook that fires, and the right(s) checked.

## File open and create

| Operation | Hook | Mode | Right(s) |
|---|---|---|---|
| `open()` / `openat()` | `security_file_open` | Live | Core + compat |
| `open()` with O_CREAT | `security_inode_create` + `security_inode_init_security` | Live | FILE_ADD_FILE on parent |
| `mkdir()` | `security_inode_mkdir` | Live | FILE_ADD_SUBDIRECTORY on parent |
| `mknod()` | `security_inode_mknod` | Live | FILE_ADD_FILE on parent |
| `symlink()` | `security_inode_symlink` | Live | FILE_ADD_FILE on parent + SeCreateSymbolicLinkPrivilege |
| `open_by_handle_at()` | Patch + `security_file_open` | Live | SeChangeNotifyPrivilege + open rights |

## Data operations (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `read()` / `pread64()` / `readv()` | `security_file_permission` | FILE_READ_DATA |
| `write()` / `writev()` | `security_file_permission` | FILE_WRITE_DATA or FILE_APPEND_DATA |
| `pwrite64()` | Patch + `security_file_permission` | FILE_WRITE_DATA |
| `pwritev()` / `pwritev2()` | Patch + `security_file_permission` | FILE_WRITE_DATA |
| `readdir` / `getdents` | `security_file_permission` | FILE_LIST_DIRECTORY |
| `sendfile()` | `security_file_permission` (both fds) | FILE_READ_DATA / FILE_WRITE_DATA |
| `copy_file_range()` | `security_file_permission` (both fds) | FILE_READ_DATA / FILE_WRITE_DATA |
| `splice()` | `security_file_permission` | FILE_READ_DATA or FILE_WRITE_DATA |
| io_uring read | `security_file_permission` | FILE_READ_DATA |
| io_uring write | Patch + `security_file_permission` | FILE_WRITE_DATA |
| AIO write | Patch + `security_file_permission` | FILE_WRITE_DATA |

## Truncate and allocate (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `ftruncate()` | `security_file_truncate` | FILE_WRITE_DATA |
| `truncate()` | `security_inode_setattr` | Live: FILE_WRITE_DATA |
| `fallocate()` extend | `security_file_permission` | FILE_WRITE_DATA or FILE_APPEND_DATA |
| `fallocate()` PUNCH_HOLE etc. | Patch | FILE_WRITE_DATA |

## Memory mapping (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `mmap()` PROT_READ | `security_mmap_file` | FILE_READ_DATA |
| `mmap()` PROT_WRITE + MAP_SHARED | `security_mmap_file` | FILE_WRITE_DATA |
| `mmap()` PROT_WRITE + MAP_PRIVATE | `security_mmap_file` | FILE_READ_DATA |
| `mmap()` PROT_EXEC | `security_mmap_file` | FILE_EXECUTE |
| `mprotect()` | `security_file_mprotect` | Same as mmap for new flags |

## Metadata fd-based (snapshot, kernel patches)

| Operation | Hook | Right(s) |
|---|---|---|
| `fstat()` | Patch: `security_file_getattr` | FILE_READ_ATTRIBUTES |
| `fchmod()` | Patch: `security_file_setattr` | WRITE_DAC |
| `fchown()` | Patch: `security_file_setattr` | WRITE_OWNER |
| `futimens()` | Patch: `security_file_setattr` | FILE_WRITE_ATTRIBUTES |
| `fgetxattr()` | Patch: `security_file_getxattr` | FILE_READ_EA (SD xattr: deny) |
| `fsetxattr()` / `fremovexattr()` | Patch: `security_file_setxattr` | FILE_WRITE_EA (SD/POSIX ACL xattr: deny) |
| `flistxattr()` | `security_inode_listxattr` | Unconditional |

## Metadata path-based (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `stat()` / `lstat()` | `security_inode_getattr` | FILE_READ_ATTRIBUTES |
| `chmod()` / `fchmodat()` | `security_inode_setattr` | WRITE_DAC |
| `chown()` / `lchown()` | `security_inode_setattr` | WRITE_OWNER |
| `utimensat()` / `utimes()` | `security_inode_setattr` | FILE_WRITE_ATTRIBUTES |
| `getxattr()` / `lgetxattr()` | `security_inode_getxattr` | FILE_READ_EA (SD xattr: deny) |
| `setxattr()` / `lsetxattr()` | `security_inode_setxattr` | FILE_WRITE_EA (SD/POSIX ACL: deny) |
| `removexattr()` | `security_inode_removexattr` | FILE_WRITE_EA (SD: deny) |
| `access()` / `faccessat()` | Patch + `security_inode_permission` | Live AccessCheck: R_OK → FILE_READ_DATA, W_OK → FILE_WRITE_DATA, X_OK → FILE_EXECUTE. F_OK (existence) → FILE_READ_ATTRIBUTES. Uses the effective token (not real credential). |

## Link operations (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `link()` / `linkat()` | `security_inode_link` | FILE_ADD_FILE on dest + FILE_WRITE_ATTRIBUTES on source |
| `unlink()` | `security_inode_unlink` | DELETE on file OR FILE_DELETE_CHILD on parent |
| `rmdir()` | `security_inode_rmdir` | DELETE on dir OR FILE_DELETE_CHILD on parent |
| `rename()` plain | `security_inode_rename` | DELETE/FILE_DELETE_CHILD on source parent + FILE_ADD_FILE (file) or FILE_ADD_SUBDIRECTORY (directory) on dest parent |
| `rename()` overwrite | `security_inode_rename` | Same + DELETE/FILE_DELETE_CHILD on existing dest |
| `renameat2(EXCHANGE)` | `security_inode_rename` | DELETE/FILE_DELETE_CHILD on both sides |
| `readlink()` | `security_inode_readlink` | FILE_READ_DATA on symlink |

## Execution

| Operation | Hook | Right(s) |
|---|---|---|
| `execve()` | `security_bprm_check` | Live: FILE_EXECUTE |
| `execveat(AT_EMPTY_PATH)` | `security_bprm_check` | Live AccessCheck for FILE_EXECUTE on the re-opened file. Future versions will check the fd's granted mask directly (snapshot mode). |
| `fexecve()` | `security_bprm_check` | Same as execveat. |

## Directory traversal

| Operation | Hook | Right(s) |
|---|---|---|
| Path resolution | `security_inode_permission` | FILE_TRAVERSE (skipped if SeChangeNotifyPrivilege held) |
| `fchdir()` normal fd | `security_file_permission` | Snapshot: FILE_TRAVERSE |
| `fchdir()` O_PATH fd | `security_inode_permission` | Live: FILE_TRAVERSE |

## Locking (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `flock(LOCK_SH)` / `F_RDLCK` | `security_file_lock` | FILE_READ_DATA |
| `flock(LOCK_EX)` / `F_WRLCK` | `security_file_lock` | FILE_WRITE_DATA or FILE_APPEND_DATA |

## Unix sockets (live)

Pathname sockets are protected via the socket file's inode SD (handled by FACS through the normal file open path). Abstract sockets store their SD on the socket's LSM security blob, stamped at `bind()` time from the binding thread's effective token.

| Operation | Hook | Right(s) |
|---|---|---|
| `bind()` abstract socket | `security_socket_bind` | Stamps SD on socket blob from caller's token. |
| `connect()` Unix stream | `security_unix_stream_connect` | AccessCheck: FILE_WRITE_DATA on socket SD. |
| `sendto()` / `sendmsg()` Unix dgram | `security_unix_may_send` | AccessCheck: FILE_WRITE_DATA on socket SD. |

## IPC (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `ioctl()` | `security_file_ioctl` | Fd must be FACS-managed (enforces ioctl-only flag). |
| `fcntl()` | `security_file_fcntl` | Fd must be FACS-managed. |
| fd transfer via `SCM_RIGHTS` | `security_file_receive` | Unconditional allow (possession is authorization). |

## Miscellaneous

| Hook | Purpose |
|---|---|
| `security_inode_follow_link` | Unconditional allow. Registered for auditability. |
| `security_inode_set_acl` | Deny POSIX ACL creation. KACS replaces POSIX ACLs. |
| `security_inode_xattr_skipcap` | Skip capability checks for xattr ops; KACS handles access control. |
| `security_inode_getsecurity` | Return SD bytes via the inode security interface. |

## Process mitigation enforcement

| Mitigation | Hook | Enforcement |
|---|---|---|
| WXP | `security_mmap_file`, `security_file_mprotect` | Reject W+X mappings and W↔X transitions. Applies to ALL mappings including anonymous (not just file-backed). `security_file_mprotect` fires for anonymous mprotect with `file=NULL`. |
| TLP | `security_mmap_file`, `security_file_mprotect` | Reject PROT_EXEC on files outside approved directory prefixes. Enforced at both mmap and mprotect (prevents mmap-without-exec then mprotect-to-exec bypass). Checked before LSV. |
| LSV | `security_mmap_file`, `security_file_mprotect` | Verify binary signature. Reject if unsigned or insufficiently trusted. Checked after TLP (TLP is a fast path rejection). |
| PIE | `security_bprm_check` | Reject ET_EXEC (non-PIE) ELF binaries at exec time. |
| CFIF | `security_task_prctl` | Block disabling of hardware indirect-branch tracking (Intel IBT). |
| CFIB | `security_task_prctl` | Block disabling of hardware shadow stack (Intel CET). |
| SML | `security_task_prctl` | Block `PR_SPEC_ENABLE` (speculation mitigation disable). |
| `no_child_process` | `security_task_alloc` | Reject fork (but not CLONE_THREAD) when flag is set. |

## Credential management

| Hook | Purpose |
|---|---|
| `security_prepare_creds` | Assert DAC bypass capabilities on new credentials. |
| `security_transfer_creds` | Transfer token reference on credential transfer. |
| `security_cred_alloc_blank` | Allocate blank credential blob. |
| `security_cred_free` | Free token reference on credential destruction. |
| `security_bprm_creds_for_exec` | Assert DAC bypass capabilities. Map privileges to capabilities. |
| `security_bprm_creds_from_file` | Suppress file capabilities, setuid, and setgid grants. |
| `security_capset` | Deny clearing DAC bypass capabilities. |
| `security_capable` | Map Linux capabilities to KACS privileges or DAC bypass. |
| `security_task_prctl` | Deny ambient capability raises and bounding set drops affecting DAC bypass capabilities. |
| `security_task_fix_setuid` | Suppress or intercept setuid-family calls. |
| `security_task_fix_setgid` | Suppress or intercept setgid-family calls. |

## Process lifecycle

| Hook | Purpose |
|---|---|
| `security_task_alloc` | Allocate PSB, inherit PIP/mitigations, create process SD. |
| `security_task_free` | Free PSB and process SD. |
| `security_task_kill` | Enforce process SD + PIP dominance on signal delivery. |
| `security_ptrace_access_check` | Enforce process SD + PIP dominance on ptrace. |
| `security_task_setnice` | Enforce process SD (PROCESS_SET_INFORMATION) + PIP. |
| `security_task_setscheduler` | Same as setnice. |
| `security_task_setioprio` | Same as setnice. |
| `security_task_prlimit` | Enforce process SD + PIP on resource limit changes. |

## Socket lifecycle

| Hook | Purpose |
|---|---|
| `security_sk_alloc` | Allocate socket security blob. |
| `security_sk_free` | Free socket security blob. |
| `security_socket_bind` | Stamp abstract socket SD at bind time. |

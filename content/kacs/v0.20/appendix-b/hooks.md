---
title: LSM Hook Matrix
order: 1
---

This is the definitive reference mapping file operations to LSM hooks and required access rights. Each entry specifies: enforcement mode (snapshot = granted mask check, live = AccessCheck against SD), the hook that fires, and the right(s) checked.

## File open and create

| Operation | Hook | Mode | Right(s) |
|---|---|---|---|
| `open()` / `openat()` | `security_file_open` | Live | Core + compat |
| `open()` with O_CREAT | `security_inode_create` + `security_inode_init_security` | Live | FILE_ADD_FILE on parent |
| `mkdir()` | `security_inode_mkdir` | Live | FILE_ADD_SUBDIRECTORY on parent |
| `mknod()` | `security_inode_mknod` | Live | FILE_ADD_FILE on parent |
| `symlink()` | `security_inode_symlink` | Live | FILE_ADD_FILE on parent |
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
| `access()` / `faccessat()` | Patch + `security_inode_permission` | See access() mapping |

## Link operations (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `link()` / `linkat()` | `security_inode_link` | FILE_ADD_FILE on dest + FILE_WRITE_ATTRIBUTES on source |
| `unlink()` | `security_inode_unlink` | DELETE on file OR FILE_DELETE_CHILD on parent |
| `rmdir()` | `security_inode_rmdir` | DELETE on dir OR FILE_DELETE_CHILD on parent |
| `rename()` plain | `security_inode_rename` | DELETE/FILE_DELETE_CHILD on source + FILE_ADD_FILE on dest |
| `rename()` overwrite | `security_inode_rename` | Same + DELETE/FILE_DELETE_CHILD on existing dest |
| `renameat2(EXCHANGE)` | `security_inode_rename` | DELETE/FILE_DELETE_CHILD on both sides |
| `readlink()` | `security_inode_readlink` | FILE_READ_DATA on symlink |

## Execution

| Operation | Hook | Right(s) |
|---|---|---|
| `execve()` | `security_bprm_check` | Live: FILE_EXECUTE |
| `execveat(AT_EMPTY_PATH)` | Patch + `security_bprm_check` | Snapshot: FILE_EXECUTE in granted mask |
| `fexecve()` | Patch + `security_bprm_check` | Snapshot: FILE_EXECUTE in granted mask |

## Directory traversal

| Operation | Hook | Right(s) |
|---|---|---|
| Path resolution | `security_inode_permission` | FILE_TRAVERSE (skipped if SeChangeNotifyPrivilege held) |
| `fchdir()` normal fd | Patch: `security_file_fchdir` | Snapshot: FILE_TRAVERSE |
| `fchdir()` O_PATH fd | `security_inode_permission` | Live: FILE_TRAVERSE |

## Locking (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `flock(LOCK_SH)` / `F_RDLCK` | `security_file_lock` | FILE_READ_DATA |
| `flock(LOCK_EX)` / `F_WRLCK` | `security_file_lock` | FILE_WRITE_DATA or FILE_APPEND_DATA |

## Unix sockets (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `connect()` Unix stream | `security_unix_stream_connect` | FILE_WRITE_DATA on socket |
| `sendto()` / `sendmsg()` Unix dgram | `security_unix_may_send` | FILE_WRITE_DATA on socket |

## Credential management

| Hook | Purpose |
|---|---|
| `security_prepare_creds` | Assert DAC bypass capabilities on new credentials. |
| `security_bprm_creds_for_exec` | Assert DAC bypass capabilities. Map privileges to capabilities. |
| `security_bprm_creds_from_file` | Suppress file capabilities, setuid, and setgid grants. |
| `security_capset` | Deny clearing DAC bypass capabilities. |
| `security_task_prctl` | Deny ambient capability raises and bounding set drops affecting DAC bypass capabilities. |

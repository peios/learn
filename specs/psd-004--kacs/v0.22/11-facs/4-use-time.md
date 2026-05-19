---
title: Use-Time Semantics
---

Every operation on an open fd is a mask check against the granted mask, with one v0.20 exception: `execveat(AT_EMPTY_PATH)` uses a live AccessCheck rather than the cached mask (see Execution below).

## Data operations

| Operation | Required right |
|---|---|
| Read | FILE_READ_DATA |
| Sequential write (non-append intent) | FILE_WRITE_DATA |
| Append-intent write (`O_APPEND` fd or `RWF_APPEND`) | FILE_APPEND_DATA or FILE_WRITE_DATA |
| Positioned write or no-append override | FILE_WRITE_DATA (denied on append-only fds) |
| Directory listing (readdir/getdents) | FILE_LIST_DIRECTORY |
| Truncate (ftruncate) | FILE_WRITE_DATA |
| fallocate allocation / extension (`ALLOCATE_RANGE`, `ALLOCATE_RANGE | KEEP_SIZE`) | FILE_APPEND_DATA or FILE_WRITE_DATA |
| fallocate mutation modes (`PUNCH_HOLE`, `ZERO_RANGE`, `COLLAPSE_RANGE`, `INSERT_RANGE`, `UNSHARE_RANGE`, `WRITE_ZEROES`) | FILE_WRITE_DATA |
| mmap PROT_READ | FILE_READ_DATA |
| mmap PROT_WRITE + MAP_SHARED | FILE_WRITE_DATA (FILE_APPEND_DATA alone is not sufficient) |
| mmap PROT_WRITE + MAP_PRIVATE | FILE_READ_DATA (copy-on-write; no write to file) |
| mmap PROT_EXEC | FILE_EXECUTE |
| mprotect | Same as mmap for new protection flags |
| flock LOCK_SH / F_RDLCK | FILE_READ_DATA |
| flock LOCK_EX / F_WRLCK | FILE_WRITE_DATA or FILE_APPEND_DATA |

## Metadata operations

| Operation | Required right |
|---|---|
| stat / lstat / path statx | FILE_READ_ATTRIBUTES |
| fstat / fd statx | FILE_READ_ATTRIBUTES |
| fstatfs / fstatfs64 | FILE_READ_ATTRIBUTES |
| path file_getattr | FILE_READ_ATTRIBUTES |
| fd file_getattr | FILE_READ_ATTRIBUTES |
| path file_setattr | FILE_WRITE_ATTRIBUTES |
| fd file_setattr | FILE_WRITE_ATTRIBUTES |
| truncate (pathname) | FILE_WRITE_DATA |
| chmod / fchmodat | WRITE_DAC |
| fchmod | WRITE_DAC |
| chown / lchown / fchownat | WRITE_OWNER |
| fchown | WRITE_OWNER |
| utimensat / utimes | FILE_WRITE_ATTRIBUTES |
| futimens | FILE_WRITE_ATTRIBUTES |
| getxattr / lgetxattr | FILE_READ_EA |
| fgetxattr | FILE_READ_EA |
| setxattr / lsetxattr / removexattr | FILE_WRITE_EA |
| fsetxattr / fremovexattr | FILE_WRITE_EA |
| listxattr / llistxattr | none |
| flistxattr | none |
| access / faccessat F_OK | FILE_READ_ATTRIBUTES |
| access / faccessat R_OK | FILE_READ_DATA |
| access / faccessat W_OK | FILE_WRITE_DATA |
| access / faccessat X_OK | FILE_EXECUTE |

Canonical SD xattr reads and writes MUST be denied unconditionally via the xattr hooks. The canonical SD xattr is `security.peios.sd`, or `system.ntfs_security` on NTFS as defined by §11.5. All SD access MUST go through `kacs_get_sd` / `kacs_set_sd`. POSIX ACL xattr writes (`system.posix_acl_access`, `system.posix_acl_default`) MUST also be denied unconditionally.

## Directory traversal

Path resolution checks `FILE_TRAVERSE` on FACS-managed directory components.
If the current effective token has `SeChangeNotifyPrivilege`, intermediate
path-resolution traverse checks are bypassed, including on directories whose
SD is missing. Explicit current-directory/root-directory changes are not
intermediate path resolution: `chdir()` and `chroot()` require a live
`FILE_TRAVERSE` check on the final directory. Normal-fd `fchdir()` checks the
fd's cached granted mask for `FILE_TRAVERSE`; O_PATH `fchdir()` performs a
live `FILE_TRAVERSE` check.

## Append-only enforcement

A handle with FILE_APPEND_DATA but not FILE_WRITE_DATA allows only true
append-intent writes. Append intent means the effective write position is
forced to EOF by `O_APPEND` or per-I/O `RWF_APPEND`, unless the same operation
uses `RWF_NOAPPEND` to negate append semantics. It MUST deny:

- Positioned writes without effective append intent (`pwrite64`, `pwritev`,
  `pwritev2` with an explicit offset, io_uring writes with an explicit offset,
  and AIO writes with an offset).
- Any write using `RWF_NOAPPEND`, including `pwritev2`, io_uring, or AIO,
  because it can negate append semantics inherited from `O_APPEND`.
- Shared writable mmap / mprotect upgrades to PROT_WRITE.
- fallocate mutation modes (PUNCH_HOLE, ZERO_RANGE, COLLAPSE_RANGE, INSERT_RANGE, UNSHARE_RANGE, WRITE_ZEROES).

## fcntl enforcement

For `F_SETFL`, KACS evaluates the mutable status flags accepted by Linux:
`O_APPEND`, `O_NONBLOCK` / `O_NDELAY`, `O_DIRECT`, and `O_NOATIME`.

- F_SETFL clearing O_APPEND: denied if fd has FILE_APPEND_DATA but not FILE_WRITE_DATA.
- F_SETFL setting O_APPEND: always allowed (privilege reduction).
- F_SETFL adding O_NOATIME: requires FILE_WRITE_ATTRIBUTES.
- F_SETFL clearing O_NOATIME: always allowed.
- F_SETFL changing only O_NONBLOCK, O_NDELAY, or O_DIRECT: no additional KACS right; ordinary Linux validation still applies.

The following non-`F_SETFL` commands are fd-local or handle-local and require
no additional KACS file right. They MUST NOT widen the cached granted mask:

| fcntl command | Required right | Rationale |
|---|---|---|
| `F_CREATED_QUERY` | none | Reports whether this fd came from a create path. |
| `F_DUPFD` / `F_DUPFD_CLOEXEC` / `F_DUPFD_QUERY` | none | Duplication and duplicate queries preserve the same open file description and granted mask. |
| `F_GETFD` / `F_SETFD` | none | Reads or changes close-on-exec state on this fd. |
| `F_GETFL` | none | Reads fd status flags. |
| `F_GETOWN` / `F_GETOWN_EX` / `F_GETOWNER_UIDS` / `F_GETSIG` | none | Reads async-notification owner state attached to this fd. |
| `F_SETOWN` / `F_SETOWN_EX` / `F_SETSIG` | none | Changes async-notification delivery state attached to this fd; Linux pid/signal validation still applies. |

The following commands are object-state queries or mutations and are checked
against the cached granted mask before Linux-specific validation:

| fcntl command | Required right |
|---|---|
| `F_GETLK` / `F_GETLK64` / `F_OFD_GETLK` | Any data right (`FILE_READ_DATA`, `FILE_WRITE_DATA`, or `FILE_APPEND_DATA`) |
| `F_GETLEASE` / `F_GETDELEG` | FILE_READ_ATTRIBUTES |
| `F_GETPIPE_SZ` | FILE_READ_ATTRIBUTES |
| `F_SETPIPE_SZ` | FILE_WRITE_ATTRIBUTES |
| `F_GET_SEALS` | FILE_READ_ATTRIBUTES |
| `F_ADD_SEALS` | FILE_WRITE_ATTRIBUTES |
| `F_GET_RW_HINT` / `F_GET_FILE_RW_HINT` | FILE_READ_ATTRIBUTES |
| `F_SET_RW_HINT` / `F_SET_FILE_RW_HINT` | FILE_WRITE_ATTRIBUTES |

Lock, lease, and delegation acquisition or release commands
(`F_SETLK`, `F_SETLKW`, `F_SETLK64`, `F_SETLKW64`, `F_OFD_SETLK`,
`F_OFD_SETLKW`, `F_SETLEASE`, `F_SETDELEG`) are allowed through the
`security_file_fcntl` hook so they can be enforced by the later
`security_file_lock` hook, which receives normalized `F_RDLCK`, `F_WRLCK`, or
`F_UNLCK` values. Unknown lock types still fail closed at that hook.

For `F_NOTIFY`, removing a watch (zero event mask, ignoring `DN_MULTISHOT`)
requires no KACS file right. Installing a watch with any known `DN_*` event
requires `FILE_LIST_DIRECTORY`. Unknown `DN_*` bits on a managed fd MUST fail
closed.

Unmanaged fds are outside the ordinary FACS handle check. Unknown managed
`fcntl` commands MUST fail closed.

## ioctl enforcement

Known ioctls are classified by required right. Unclassified ioctls fall back
to: allowed if the fd has at least one data right (FILE_READ_DATA,
FILE_WRITE_DATA, or FILE_APPEND_DATA).

The 32-bit compat aliases for the listed commands use the same required right
as their native command. This includes `FS_IOC32_GETFLAGS`,
`FS_IOC32_SETFLAGS`, `FS_IOC32_GETVERSION`, `FS_IOC32_SETVERSION`, and the
compat `FS_IOC_*_32` preallocation commands.

### FD-local ioctl commands

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FIOCLEX` / `FIONCLEX` | none | Changes close-on-exec state on this fd. |
| `FIONBIO` | none | Changes nonblocking state; no KACS file right is widened. |
| `FIOASYNC` | none | Changes async notification state; Linux/fops validation still applies. |

### Common VFS ioctls

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FIBMAP` | FILE_READ_DATA | Reads block mapping. |
| `FIGETBSZ` | FILE_READ_ATTRIBUTES | Reads filesystem block size. |
| `FIFREEZE` / `FITHAW` | FILE_WRITE_ATTRIBUTES | Mutates filesystem operational state; Linux CAP_SYS_ADMIN checks still apply. |
| `FITRIM` | FILE_WRITE_ATTRIBUTES | Trims/discards free filesystem ranges; Linux CAP_SYS_ADMIN checks still apply. |
| `FS_IOC_GETFSUUID` | FILE_READ_ATTRIBUTES | Reads filesystem UUID. |
| `FS_IOC_GETFSSYSFSPATH` | FILE_READ_ATTRIBUTES | Reads filesystem sysfs/debugfs path metadata. |
| `FS_IOC_GETLBMD_CAP` | FILE_READ_ATTRIBUTES | Reads logical-block metadata capability details. |

### Classified file/object ioctls

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FS_IOC_FIEMAP` | FILE_READ_DATA | Reads extent layout |
| `FIONREAD` | FILE_READ_DATA | Reads available byte count |
| `FS_IOC_GETFLAGS` | FILE_READ_ATTRIBUTES | Reads inode flags (immutable, append, etc.) |
| `FS_IOC_SETFLAGS` | FILE_WRITE_ATTRIBUTES | Modifies inode flags |
| `FS_IOC_GETVERSION` | FILE_READ_ATTRIBUTES | Reads inode generation number |
| `FS_IOC_SETVERSION` | FILE_WRITE_ATTRIBUTES | Modifies inode generation number |
| `FS_IOC_RESVSP` / `FS_IOC_RESVSP64` | FILE_APPEND_DATA or FILE_WRITE_DATA | Reserves/preallocates file space without arbitrary data overwrite. |
| `FS_IOC_UNRESVSP` / `FS_IOC_UNRESVSP64` | FILE_WRITE_DATA | Deallocates file space / punches holes. |
| `FS_IOC_ZERO_RANGE` | FILE_WRITE_DATA | Zeroes file range. |
| `FICLONE` | FILE_WRITE_DATA | Copy-on-write clone into target file |
| `FICLONERANGE` | FILE_WRITE_DATA | Partial clone into target file |
| `FIDEDUPERANGE` | FILE_WRITE_DATA | Deduplicate shared extents |
| `FIOQSIZE` | FILE_READ_ATTRIBUTES | Query object size |
| `FS_IOC_FSGETXATTR` | FILE_READ_ATTRIBUTES | Read extended file attributes (project ID, etc.) |
| `FS_IOC_FSSETXATTR` | FILE_WRITE_ATTRIBUTES | Write extended file attributes |
| `FS_IOC_GETFSLABEL` | FILE_READ_ATTRIBUTES | Read filesystem label. |
| `FS_IOC_SETFSLABEL` | FILE_WRITE_ATTRIBUTES | Set filesystem label. |
| `FS_IOC_GET_ENCRYPTION_PWSALT` | FILE_READ_ATTRIBUTES | Reads encryption policy salt. |
| `FS_IOC_GET_ENCRYPTION_POLICY` | FILE_READ_ATTRIBUTES | Read encryption policy |
| `FS_IOC_GET_ENCRYPTION_POLICY_EX` | FILE_READ_ATTRIBUTES | Read extended encryption policy. |
| `FS_IOC_SET_ENCRYPTION_POLICY` | FILE_WRITE_ATTRIBUTES | Set encryption policy |
| `FS_IOC_ADD_ENCRYPTION_KEY` | FILE_WRITE_ATTRIBUTES | Mutates filesystem encryption key state. |
| `FS_IOC_REMOVE_ENCRYPTION_KEY` | FILE_WRITE_ATTRIBUTES | Mutates filesystem encryption key state. |
| `FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS` | FILE_WRITE_ATTRIBUTES | Mutates filesystem encryption key state. |
| `FS_IOC_GET_ENCRYPTION_KEY_STATUS` | FILE_READ_ATTRIBUTES | Reads filesystem encryption key state. |
| `BLKGETSIZE64` | FILE_READ_ATTRIBUTES | Block device size query |
| `BLKFLSBUF` | FILE_WRITE_DATA | Flush block device buffers |

### Classified directory ioctls

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FS_IOC_GETFLAGS` | FILE_READ_ATTRIBUTES | Same as file |
| `FS_IOC_SETFLAGS` | FILE_WRITE_ATTRIBUTES | Same as file |

### Unclassified ioctls

Any ioctl not in the tables above is allowed if the fd carries at least one data right (FILE_READ_DATA, FILE_WRITE_DATA, or FILE_APPEND_DATA). Future versions will expand the classified list and may deny unclassified ioctls.

**Device nodes, pipes, sockets:** unclassified/device-specific ioctls are
allowed if the fd has at least one data right. Device-specific ioctl semantics
are outside FACS scope — the device node's SD is the FACS authorization
boundary, and Linux device-specific validation may still deny the operation.

## Execution

Execution is a two-layer check:

- **Mode execute bit** — prerequisite. "This file is a program." Set by package managers and `chmod +x`. Applies only to `execve` / `execveat`, not to `mmap(PROT_EXEC)`.
- **SD FILE_EXECUTE** — access control. "This principal may execute this file." Gates both `execve` and `mmap(PROT_EXEC)`.

For `execve`: both +x AND FILE_EXECUTE MUST be true. For `mmap(PROT_EXEC)`: only FILE_EXECUTE is checked.

For fd-based exec (`execveat` with AT_EMPTY_PATH) in v0.20, a live AccessCheck for FILE_EXECUTE is performed on the re-opened file. O_PATH fds use the same live AccessCheck. Future versions will check the fd's cached granted mask directly (snapshot mode).

> [!INFORMATIVE]
> Mode bits are cosmetic for read/write authorization but retain security significance for execution. Only the execute bit has semantic meaning under FACS.

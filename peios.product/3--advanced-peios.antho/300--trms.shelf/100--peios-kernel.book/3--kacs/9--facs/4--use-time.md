---
title: Use-Time Semantics
description: Every operation on an open descriptor is a mask check against the granted mask — data, metadata, traversal, append-only, fcntl and ioctl.
---

Every operation on an open descriptor is a mask check against the
granted mask, with one exception: `execveat(AT_EMPTY_PATH)` uses a
live AccessCheck.

## Data operations

| Operation | Required right |
|---|---|
| Read | `FILE_READ_DATA` |
| Sequential write, no append intent | `FILE_WRITE_DATA` |
| Append-intent write (`O_APPEND` descriptor or `RWF_APPEND`) | `FILE_APPEND_DATA` or `FILE_WRITE_DATA` |
| Positioned write, or a no-append override | `FILE_WRITE_DATA` — denied on append-only descriptors |
| Directory listing | `FILE_LIST_DIRECTORY` |
| `ftruncate` | `FILE_WRITE_DATA` |
| `fallocate` allocation (`ALLOCATE_RANGE`, with or without `KEEP_SIZE`) | `FILE_APPEND_DATA` or `FILE_WRITE_DATA` |
| `fallocate` mutation (`PUNCH_HOLE`, `ZERO_RANGE`, `COLLAPSE_RANGE`, `INSERT_RANGE`, `UNSHARE_RANGE`, `WRITE_ZEROES`) | `FILE_WRITE_DATA` |
| `mmap PROT_READ` | `FILE_READ_DATA` |
| `mmap PROT_WRITE \| MAP_SHARED` | `FILE_WRITE_DATA` — `FILE_APPEND_DATA` alone is insufficient |
| `mmap PROT_WRITE \| MAP_PRIVATE` | `FILE_READ_DATA` — copy-on-write, no write to the file |
| `mmap PROT_EXEC` | `FILE_EXECUTE` |
| `mprotect` | As `mmap`, for the new protection flags |
| `flock LOCK_SH` / `F_RDLCK` | `FILE_READ_DATA` |
| `flock LOCK_EX` / `F_WRLCK` | `FILE_WRITE_DATA` or `FILE_APPEND_DATA` |
| `fsync` / `fdatasync` | `SYNCHRONIZE` |

A `fallocate` mode outside the supported set fails closed, and
`PUNCH_HOLE` additionally requires `KEEP_SIZE`.

## Metadata operations

| Operation | Required right |
|---|---|
| `stat` / `lstat` / path `statx` | `FILE_READ_ATTRIBUTES` |
| `fstat` / descriptor `statx` | `FILE_READ_ATTRIBUTES` |
| `fstatfs` | `FILE_READ_ATTRIBUTES` |
| path and descriptor `file_getattr` | `FILE_READ_ATTRIBUTES` |
| path and descriptor `file_setattr` | `FILE_WRITE_ATTRIBUTES` |
| `truncate` by pathname | `FILE_WRITE_DATA` |
| `chmod` / `fchmodat` / `fchmod` | `WRITE_DAC` |
| `chown` / `lchown` / `fchownat` / `fchown` | `WRITE_OWNER` |
| `utimensat` / `utimes` / `futimens` | `FILE_WRITE_ATTRIBUTES` |
| `getxattr` / `lgetxattr` / `fgetxattr` | `FILE_READ_EA` |
| `setxattr` / `lsetxattr` / `removexattr` / `fsetxattr` / `fremovexattr` | `FILE_WRITE_EA` |
| `listxattr` / `llistxattr` / `flistxattr` | none |
| `access` / `faccessat` `F_OK` | `FILE_READ_ATTRIBUTES` |
| `access` / `faccessat` `R_OK` | `FILE_READ_DATA` |
| `access` / `faccessat` `W_OK` | `FILE_WRITE_DATA` |
| `access` / `faccessat` `X_OK` | `FILE_EXECUTE` |

Reads and writes of the canonical descriptor xattr are denied
unconditionally through the xattr hooks — `security.peios.sd`, or
`system.ntfs_security` on NTFS. All descriptor access goes through
`kacs_get_sd` and `kacs_set_sd`. POSIX ACL xattr writes are denied
unconditionally too, with `EOPNOTSUPP` rather than `EACCES` so that
probe-then-tolerate callers behave sensibly.

## Directory traversal

Path resolution checks `FILE_TRAVERSE` on managed directory
components. A token holding `SeChangeNotifyPrivilege` bypasses the
intermediate checks, including on directories whose descriptor is
missing.

Explicit changes of the current or root directory are not intermediate
resolution: `chdir()` and `chroot()` take a live `FILE_TRAVERSE` check
on the final directory, and the privilege bypass does not apply
(§3.4.2). An ordinary `fchdir()` checks the descriptor's cached mask;
an `O_PATH` `fchdir()` runs live.

## Watch placement

Placing a watch — `inotify_add_watch()`, `fanotify_mark()` on an
inode, `F_NOTIFY` — is a read of the object by other means: a watch on
a directory reveals the names of its children as they come and go, a
watch on a file reports its activity. Linux gates it on read
permission, but under KACS a bare `MAY_READ` never reaches a
descriptor (read rights are decided at open), so the `path_notify`
hook checks the read-class right live against the object's own
descriptor: `FILE_LIST_DIRECTORY` for a directory, `FILE_READ_DATA`
for anything else. A denial is `EACCES`, and `SeChangeNotifyPrivilege`
does not bypass it — that privilege covers traversal, not reading.

Mount, filesystem and mount-namespace marks are not object watches and
have no single descriptor to check. Linux requires `CAP_SYS_ADMIN` for
them, and for the fanotify permission classes (`FAN_CLASS_CONTENT`,
`FAN_CLASS_PRE_CONTENT` — the ones whose holder can veto or delay
opens and reads system-wide); the capability switchboard (§3.10.2)
resolves that to `SeTcbPrivilege`, so these are TCB-only. PIP
dominance is not part of the decision: a permission-event holder
intercepts opens of the *object*, never the opening process, and a
holder that is by construction TCB dominates every process anyway.

## Append-only enforcement

A handle carrying `FILE_APPEND_DATA` but not `FILE_WRITE_DATA` allows
only true append-intent writes. Append intent means the effective
write position is forced to end-of-file by `O_APPEND` or per-I/O
`RWF_APPEND`, and is not negated by `RWF_NOAPPEND` on the same
operation. Requesting both `RWF_APPEND` and `RWF_NOAPPEND` together
fails with `EACCES`.

Denied on such a handle: positioned writes without effective append
intent — `pwrite64`, `pwritev`, `pwritev2` with an explicit offset,
io_uring writes with an explicit offset, and AIO writes with an
offset; any write using `RWF_NOAPPEND`, since it can negate append
semantics inherited from `O_APPEND`; shared writable `mmap` and
`mprotect` upgrades to `PROT_WRITE`; and the `fallocate` mutation
modes.

## fcntl

For `F_SETFL`, KACS evaluates the mutable status flags Linux accepts —
`O_APPEND`, `O_NONBLOCK`/`O_NDELAY`, `O_DIRECT`, `O_NOATIME`.
Clearing `O_APPEND` is denied on a handle with `FILE_APPEND_DATA` but
not `FILE_WRITE_DATA`; setting it is always allowed, being a privilege
reduction. Adding `O_NOATIME` requires `FILE_WRITE_ATTRIBUTES` and
clearing it is always allowed. Changing only `O_NONBLOCK`, `O_NDELAY`
or `O_DIRECT` needs no KACS right, though ordinary Linux validation
still applies.

These commands are descriptor-local and require no KACS right, and
none of them widens the cached mask: `F_CREATED_QUERY`; `F_DUPFD`,
`F_DUPFD_CLOEXEC` and `F_DUPFD_QUERY`, which preserve the same file
description and mask; `F_GETFD` and `F_SETFD`; `F_GETFL`; and the
async-notification set `F_GETOWN`, `F_GETOWN_EX`, `F_GETOWNER_UIDS`,
`F_GETSIG`, `F_SETOWN`, `F_SETOWN_EX` and `F_SETSIG`, where Linux pid
and signal validation still applies.

These are object-state queries or mutations, checked against the
cached mask before Linux-specific validation:

| Command | Required right |
|---|---|
| `F_GETLK` / `F_GETLK64` / `F_OFD_GETLK` | Any data right |
| `F_GETLEASE` / `F_GETDELEG` | `FILE_READ_ATTRIBUTES` |
| `F_GETPIPE_SZ` | `FILE_READ_ATTRIBUTES` |
| `F_SETPIPE_SZ` | `FILE_WRITE_ATTRIBUTES` |
| `F_GET_SEALS` | `FILE_READ_ATTRIBUTES` |
| `F_ADD_SEALS` | `FILE_WRITE_ATTRIBUTES` |
| `F_GET_RW_HINT` / `F_GET_FILE_RW_HINT` | `FILE_READ_ATTRIBUTES` |
| `F_SET_RW_HINT` / `F_SET_FILE_RW_HINT` | `FILE_WRITE_ATTRIBUTES` |

Lock, lease and delegation commands — `F_SETLK`, `F_SETLKW`,
`F_SETLK64`, `F_SETLKW64`, `F_OFD_SETLK`, `F_OFD_SETLKW`,
`F_SETLEASE`, `F_SETDELEG` — pass through the fcntl hook so that the
later file-lock hook can enforce them against normalised `F_RDLCK`,
`F_WRLCK` or `F_UNLCK` values. An unknown lock type fails closed
there.

For `F_NOTIFY`, removing a watch — a zero event mask, ignoring
`DN_MULTISHOT` — requires nothing. Installing one with any known `DN_*`
event requires `FILE_LIST_DIRECTORY`. Unknown `DN_*` bits on a managed
descriptor fail closed.

Unmanaged descriptors sit outside the handle check entirely, and an
unknown fcntl command on a managed one fails closed.

## ioctl

Known ioctls are classified by required right; an unclassified one is
allowed if the descriptor carries at least one data right. The 32-bit
compat aliases take the same right as their native command, including
`FS_IOC32_GETFLAGS`, `FS_IOC32_SETFLAGS`, `FS_IOC32_GETVERSION`,
`FS_IOC32_SETVERSION` and the compat preallocation commands.

**Descriptor-local**, requiring nothing: `FIOCLEX` and `FIONCLEX`,
which change close-on-exec state; `FIONBIO`, which changes nonblocking
state; and `FIOASYNC`, which changes async notification state with
Linux and fops validation still applying.

**Common VFS:**

| ioctl | Required right |
|---|---|
| `FIBMAP` | `FILE_READ_DATA` |
| `FIGETBSZ` | `FILE_READ_ATTRIBUTES` |
| `FIFREEZE` / `FITHAW` | `FILE_WRITE_ATTRIBUTES` |
| `FITRIM` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_GETFSUUID` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_GETFSSYSFSPATH` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_GETLBMD_CAP` | `FILE_READ_ATTRIBUTES` |

`FIFREEZE`, `FITHAW` and `FITRIM` mutate filesystem operational
state, and Linux's own `CAP_SYS_ADMIN` checks still apply on top.

**File and object:**

| ioctl | Required right |
|---|---|
| `FS_IOC_FIEMAP` | `FILE_READ_DATA` |
| `FIONREAD` | `FILE_READ_DATA` on a regular file; any data right otherwise |
| `FS_IOC_GETFLAGS` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_SETFLAGS` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_GETVERSION` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_SETVERSION` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_RESVSP` / `FS_IOC_RESVSP64` | `FILE_APPEND_DATA` or `FILE_WRITE_DATA` |
| `FS_IOC_UNRESVSP` / `FS_IOC_UNRESVSP64` | `FILE_WRITE_DATA` |
| `FS_IOC_ZERO_RANGE` | `FILE_WRITE_DATA` |
| `FICLONE` / `FICLONERANGE` | `FILE_WRITE_DATA` |
| `FIDEDUPERANGE` | `FILE_WRITE_DATA` |
| `FIOQSIZE` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_FSGETXATTR` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_FSSETXATTR` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_GETFSLABEL` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_SETFSLABEL` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_GET_ENCRYPTION_PWSALT` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_GET_ENCRYPTION_POLICY` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_GET_ENCRYPTION_POLICY_EX` | `FILE_READ_ATTRIBUTES` |
| `FS_IOC_SET_ENCRYPTION_POLICY` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_ADD_ENCRYPTION_KEY` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_REMOVE_ENCRYPTION_KEY` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS` | `FILE_WRITE_ATTRIBUTES` |
| `FS_IOC_GET_ENCRYPTION_KEY_STATUS` | `FILE_READ_ATTRIBUTES` |
| `BLKGETSIZE64` | `FILE_READ_ATTRIBUTES` |
| `BLKFLSBUF` | `FILE_WRITE_DATA` |

On directories, `FS_IOC_GETFLAGS` and `FS_IOC_SETFLAGS` take the same
rights as on files.

Anything unclassified is allowed on any data right. For device nodes,
pipes and sockets, device-specific ioctl semantics are outside FACS
scope: the node's descriptor is the authorization boundary, and
Linux's device-specific validation may still deny.

A pinned inode (§3.6) narrows all of this. Every content-, range- or
allocation-mutating ioctl is rejected on one, and so is every ioctl
the classifier does not recognise — unknown ioctls fail closed there
rather than falling back to the data-right rule.

## Execution

Execution is nominally a two-layer check. The **mode execute bit** is
the prerequisite meaning "this file is a program", set by package
managers and `chmod +x`, applying to `execve` and `execveat` but not
to `mmap(PROT_EXEC)`. The **descriptor's `FILE_EXECUTE`** is the
access control, gating both.

KACS enforces only the second. Nothing in the kernel module tests the
execute mode bit; the prerequisite survives because Linux's own
`generic_permission()` refuses `MAY_EXEC` on a file with no execute
bit set, by way of `capable_wrt_inode_uidgid(CAP_DAC_OVERRIDE)`. The
`+x` requirement is therefore a Linux DAC property that KACS inherits
rather than a FACS rule, and it is one of the few decisions where mode
bits still matter (§3.10.2).

For descriptor-based exec — `execveat` with `AT_EMPTY_PATH`, including
on `O_PATH` handles — a live AccessCheck for `FILE_EXECUTE` runs
against the re-opened file rather than the cached mask being consulted.

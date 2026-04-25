---
title: Use-Time Semantics
---

Every operation on an open fd is a mask check against the granted mask, with one v0.20 exception: `execveat(AT_EMPTY_PATH)` uses a live AccessCheck rather than the cached mask (see Execution below).

## Data operations

| Operation | Required right |
|---|---|
| Read | FILE_READ_DATA |
| Sequential write (non-append) | FILE_WRITE_DATA |
| Sequential write (O_APPEND fd) | FILE_APPEND_DATA or FILE_WRITE_DATA |
| Positioned write (pwrite family) | FILE_WRITE_DATA (denied on append-only fds) |
| Directory listing (readdir/getdents) | FILE_LIST_DIRECTORY |
| Truncate (ftruncate) | FILE_WRITE_DATA |
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
| fstat | FILE_READ_ATTRIBUTES |
| fchmod | WRITE_DAC |
| fchown | WRITE_OWNER |
| futimens | FILE_WRITE_ATTRIBUTES |
| fgetxattr | FILE_READ_EA |
| fsetxattr / fremovexattr | FILE_WRITE_EA |

SD xattr reads and writes (`security.peios.sd`, `system.ntfs_security`) MUST be denied unconditionally via the xattr hooks. All SD access MUST go through `kacs_get_sd` / `kacs_set_sd`. POSIX ACL xattr writes (`system.posix_acl_access`, `system.posix_acl_default`) MUST also be denied unconditionally.

## Append-only enforcement

A handle with FILE_APPEND_DATA but not FILE_WRITE_DATA allows appends but MUST deny:

- Positioned writes (pwrite, pwritev, pwritev2 with RWF_NOAPPEND, io_uring writes with offset, AIO writes with offset).
- Shared writable mmap / mprotect upgrades to PROT_WRITE.
- fallocate mutation modes (PUNCH_HOLE, ZERO_RANGE, COLLAPSE_RANGE, INSERT_RANGE).

## fcntl enforcement

- F_SETFL clearing O_APPEND: denied if fd has FILE_APPEND_DATA but not FILE_WRITE_DATA.
- F_SETFL setting O_APPEND: always allowed (privilege reduction).
- F_SETFL adding O_NOATIME: requires FILE_WRITE_ATTRIBUTES.

## ioctl enforcement

**Regular files and directories:** known ioctls are classified by required right. Unclassified ioctls fall back to: allowed if the fd has at least one data right (FILE_READ_DATA, FILE_WRITE_DATA, or FILE_APPEND_DATA).

### Classified file ioctls

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FIEMAP` | FILE_READ_DATA | Reads extent layout |
| `FIONREAD` | FILE_READ_DATA | Reads available byte count |
| `FS_IOC_GETFLAGS` | FILE_READ_ATTRIBUTES | Reads inode flags (immutable, append, etc.) |
| `FS_IOC_SETFLAGS` | FILE_WRITE_ATTRIBUTES | Modifies inode flags |
| `FS_IOC_GETVERSION` | FILE_READ_ATTRIBUTES | Reads inode generation number |
| `FS_IOC_SETVERSION` | FILE_WRITE_ATTRIBUTES | Modifies inode generation number |
| `FICLONE` | FILE_WRITE_DATA | Copy-on-write clone into target file |
| `FICLONERANGE` | FILE_WRITE_DATA | Partial clone into target file |
| `FIDEDUPERANGE` | FILE_WRITE_DATA | Deduplicate shared extents |
| `FIOQSIZE` | FILE_READ_ATTRIBUTES | Query object size |
| `FS_IOC_FSGETXATTR` | FILE_READ_ATTRIBUTES | Read extended file attributes (project ID, etc.) |
| `FS_IOC_FSSETXATTR` | FILE_WRITE_ATTRIBUTES | Write extended file attributes |
| `FS_IOC_GET_ENCRYPTION_POLICY` | FILE_READ_ATTRIBUTES | Read encryption policy |
| `FS_IOC_SET_ENCRYPTION_POLICY` | FILE_WRITE_ATTRIBUTES | Set encryption policy |
| `BLKGETSIZE64` | FILE_READ_ATTRIBUTES | Block device size query |
| `BLKFLSBUF` | FILE_WRITE_DATA | Flush block device buffers |

### Classified directory ioctls

| ioctl | Required right | Rationale |
|-------|---------------|-----------|
| `FS_IOC_GETFLAGS` | FILE_READ_ATTRIBUTES | Same as file |
| `FS_IOC_SETFLAGS` | FILE_WRITE_ATTRIBUTES | Same as file |

### Unclassified ioctls

Any ioctl not in the tables above is allowed if the fd carries at least one data right (FILE_READ_DATA, FILE_WRITE_DATA, or FILE_APPEND_DATA). Future versions will expand the classified list and may deny unclassified ioctls.

**Device nodes, pipes, sockets:** ioctls are allowed if the fd has at least one data right. Device-specific ioctl semantics are outside FACS scope — the device node's SD is the authorization boundary.

## Execution

Execution is a two-layer check:

- **Mode execute bit** — prerequisite. "This file is a program." Set by package managers and `chmod +x`. Applies only to `execve` / `execveat`, not to `mmap(PROT_EXEC)`.
- **SD FILE_EXECUTE** — access control. "This principal may execute this file." Gates both `execve` and `mmap(PROT_EXEC)`.

For `execve`: both +x AND FILE_EXECUTE MUST be true. For `mmap(PROT_EXEC)`: only FILE_EXECUTE is checked.

For fd-based exec (`execveat` with AT_EMPTY_PATH) in v0.20, a live AccessCheck for FILE_EXECUTE is performed on the re-opened file. O_PATH fds use the same live AccessCheck. Future versions will check the fd's cached granted mask directly (snapshot mode).

> [!INFORMATIVE]
> Mode bits are cosmetic for read/write authorization but retain security significance for execution. Only the execute bit has semantic meaning under FACS.

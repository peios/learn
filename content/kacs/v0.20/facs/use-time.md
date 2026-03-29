---
title: Use-Time Semantics
order: 4
---

Every operation on an open fd is a mask check against the granted mask:

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

**Regular files and directories:** classified allowlist. Known ioctls are mapped to specific rights. Unclassified ioctls MUST be denied.

**Device nodes, pipes, sockets:** ioctls are allowed if the fd has at least one data right. Device-specific ioctl semantics are outside FACS scope — the device node's SD is the authorization boundary.

## Execution

Execution is a two-layer check:

- **Mode execute bit** — prerequisite. "This file is a program." Set by package managers and `chmod +x`. Applies only to `execve` / `execveat`, not to `mmap(PROT_EXEC)`.
- **SD FILE_EXECUTE** — access control. "This principal may execute this file." Gates both `execve` and `mmap(PROT_EXEC)`.

For `execve`: both +x AND FILE_EXECUTE MUST be true. For `mmap(PROT_EXEC)`: only FILE_EXECUTE is checked.

For fd-based exec (`execveat` with AT_EMPTY_PATH), FILE_EXECUTE MUST be in the fd's granted mask. For O_PATH fds, a live AccessCheck is performed instead.

> [!INFORMATIVE]
> Mode bits are cosmetic for read/write authorization but retain security significance for execution. Only the execute bit has semantic meaning under FACS.

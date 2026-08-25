---
title: Failure Modes
description: Every condition under which a stratafs operation fails and the error it produces, from mount time through resolution and mutation.
---

This section consolidates the conditions under which a stratafs
operation fails and the error each produces. The sections above remain
authoritative for the conditions themselves.

## Mount-time

| Condition | Error |
|---|---|
| Caller lacks the access to resolve a stratum path or read its attributes | `EACCES` |
| Empty stratum stack, or `strata=` absent | `EINVAL` |
| Stack longer than 16 strata | `EINVAL` |
| More than one stratum carries `create` | `EINVAL` |
| A stratum carries both `create` and `ro` | `EINVAL` |
| The same directory appears twice in the stack | `EINVAL` |
| Any malformed `strata=` value (§4.2.2) | `EINVAL` |
| `strata=` supplied on a remount | `EINVAL` |
| An allocation failure while parsing | `ENOMEM` |
| A create-bearing stack established outside the initial user namespace, or without `CAP_SYS_ADMIN` there | `EPERM` |
| A stratum path names a non-directory | `ENOTDIR` |
| A stratum is absent without `am` | `ENOENT` |
| A stratum lies within the mount point, or within another stratafs mount whose strata include this mount point | `ELOOP` |
| The composed stack reaches the kernel's maximum stacking depth | `ELOOP` |
| Sixteen consecutive collisions allocating a mount cookie | `EAGAIN` |

The option-only conditions are decided before any path is touched, and
the `EPERM` admission test before any path is resolved. The per-path
conditions follow. §4.2.3 records the one place the specified ordering
is not achieved.

## Resolution

| Condition | Error |
|---|---|
| No participating stratum holds the name | `ENOENT` |
| An ancestor of the path is masked by a non-directory provider | `ENOTDIR` |
| Operation requires a non-directory; provider is a directory | `EISDIR` |
| Traverse or list refused on any participating directory | `EACCES` |
| A stratum walk fails for a reason other than absence | that error |
| A joined stratum path or child relative path exceeds `PATH_MAX` | `ENAMETOOLONG` |
| A task re-enters the same superblock while resolving | `ELOOP` |

## Mutation

| Condition | Error |
|---|---|
| Provider will not accept modification, and no create stratum has higher precedence | `EROFS` |
| Any mutation on a read-only-mounted stratafs | `EROFS` |
| Creation, unnamed-file creation, or unnamed-file link with no create stratum, or it absent | `EROFS` |
| Create stratum holds a path component as a non-directory | `ENOTDIR` |
| Exclusive creation where any stratum holds the name | `EEXIST` |
| Copy-up cannot preserve an extended attribute | `EIO` |
| Copy-up cannot preserve the descriptor | `EACCES`, `EOPNOTSUPP`, `EINVAL`, `ESTALE` or `ENOMEM`, as KACS reported it |
| Copy-up for a descriptor whose object is no longer the provider, or whose target name is taken at publication | `ESTALE` |
| Copy-up of a device node, FIFO or socket | `EROFS` |
| Unlink where the provider will not accept modification | `EROFS`, or `EPERM` where the provider inode is immutable |
| Rmdir where another stratum holds entries within | `ENOTEMPTY` |
| Rmdir or directory rename where list is refused on a participant | `EACCES` |
| Modifying a special file's mode, descriptor or extended attributes where its provider will not accept modification | `EROFS` |
| Establishing a shared write-capable mapping where routing yields read-only | `EROFS` |
| Replacing disposition where §4.5.4 would refuse the removal, or where a stratum above the create stratum would still hold the name | `EROFS` |
| Replacing disposition on anything but a regular file | `EOPNOTSUPP` |
| Rename where the source's provider will not accept modification | `EROFS` |
| Rename where a stratum above the source's provider provides the destination | `EROFS` |
| Rename where the source's provider does not hold the destination's directory | `EXDEV` |
| Rename of a directory containing entries from other strata | `EXDEV` |
| Rename of a non-directory onto a directory provider | `EISDIR` |
| Rename of a directory onto a non-directory provider | `ENOTDIR` |
| Rename onto a destination directory not empty across every stratum | `ENOTEMPTY` |
| `RENAME_NOREPLACE` where any stratum holds the destination | `EEXIST` |
| `RENAME_EXCHANGE` where the two names are not provided by one stratum that accepts modification | `EROFS` |
| `RENAME_EXCHANGE` where another stratum holds entries under either directory name | `EXDEV` |
| `RENAME_WHITEOUT` | `EINVAL` |
| Hard link whose source's provider will not accept modification, or does not hold the destination's directory | `EXDEV` |
| Hard link where any stratum holds the destination | `EEXIST` |
| Linking an unnamed file into a different mount | `EXDEV` |
| A dentry whose private state is missing, or whose provider identity no longer matches | `ESTALE` |
| `ioctl` on a regular file | `ENOTTY`, or `ENOIOCTLCMD` for the compat form |
| `remap_file_range` with flags outside dedupe and advisory | `EINVAL` |

## Interface

| Condition | Error |
|---|---|
| Set or remove of any reserved attribute | `EPERM` |
| Read of a reserved attribute other than `origin` | `ENODATA` |
| Origin read where read-EA is refused on any participant | `EACCES` |
| Origin read into an undersized buffer | `ERANGE` |
| Freezing the filesystem | `EOPNOTSUPP` |
| Reading a mount's policy without TCB privilege | refused by KACS |

## Intended divergences

None of the following is a defect. Each is described above, and each
follows from stratafs having no way to record that a name should be
absent, or from a merged path standing for objects in more than one
stratum.

- **Removing a name may not remove it from the view.** Where a lower
  stratum also holds the name, it becomes the provider and the name
  remains, now resolving to different content (§4.5.4).
- **A name may be unremovable.** Where the provider will not accept
  modification, removal fails however the caller is privileged
  (§4.5.4).
- **Rename may be refused for an unmodified file.** Where the source's
  provider will not accept modification, rename fails rather than
  silently copying (§4.5.5).
- **Hard links may be refused within one directory.** Where the
  source's provider will not accept modification, linking fails with
  `EXDEV` (§4.5.6).
- **An object's inode number may change.** Where the provider for a
  path changes, a new inode is presented (§4.4.3).
- **Two callers may hold non-contending locks on one path.** Locks are
  held on the object a descriptor resolved to, so callers who opened
  either side of a change of provider — including one caused by a
  copy-up neither of them performed — have locked different objects
  (§4.5.7).
- **Copy-up severs hard links.** Two names that shared an object in a
  lower stratum, and compared equal by inode number, refer to different
  objects once one of them is written through the mount; only the
  written one is copied up (§4.5.2).
- **An open may succeed where the first write then fails.** Routing
  happens when a modifying operation is performed, not at open, so an
  open for writing against a provider that will not accept modification
  succeeds and the `EROFS` arrives at the write, the truncate, or the
  attempt to establish a shared writable mapping (§4.5.1).
- **A copy-up moves an object out from under descriptors already open
  on it.** Only the descriptor whose operation caused the copy-up refers
  to the copy; others continue to refer to the original, and locks held
  on it stay there (§4.5.1, §4.5.7).
- **A write may fail `ESTALE` on a descriptor that was valid when
  opened.** Where another descriptor, another mount, or a direct writer
  has since caused that name to be provided by a different object, a
  copy-up cannot proceed and the caller must reopen (§4.5.2).
- **`fstat` and `stat` may report different inode numbers for one
  file.** After a copy-up, the descriptor that caused it keeps the inode
  it was opened against while a fresh resolution of the path yields a
  new one, so the two disagree for as long as that descriptor lives —
  though both name the copy (§4.4.3).
- **A directory's link count is always 1.** The true count of
  subdirectories spans strata and cannot be maintained (§4.4.3).
- **Directory positions do not survive a reopen.** A `readdir` offset
  is an ordinal into a per-descriptor capture, carrying no provider
  cookie (§4.3.4).

Every one of the first four is the result of refusing to invent a
hidden record — a whiteout — that would make an entry in someone else's
directory unreachable without their knowledge. The alternative buys
POSIX fidelity at the cost of a stratum no longer meaning what its
owner wrote in it, which is the property §4.2.1 exists to protect.

---
title: KACS-Native Open
---

Peios provides a KACS-native open syscall that takes an explicit desired access mask. The caller names every right it will need: FILE_READ_DATA, FILE_WRITE_DATA, WRITE_DAC, READ_CONTROL, or any combination. AccessCheck evaluates the full requested mask at open time. If every requested right is granted, the fd's granted mask is set to the requested mask. If any requested right is denied, the open fails.

`MAXIMUM_ALLOWED` MAY be combined with at least one concrete data right or
`FILE_EXECUTE`. The concrete data/execute bits define the Linux `f_mode` for
the returned fd and MUST be granted; `MAXIMUM_ALLOWED` causes the fd's cached
KACS granted mask to be the maximum granted mask computed by AccessCheck.
`MAXIMUM_ALLOWED` by itself is invalid for `kacs_open` because it does not
define a Linux fd mode and fails with `-EINVAL`.

## Required data right

The KACS-native open MUST require at least one data right (FILE_READ_DATA, FILE_WRITE_DATA, FILE_APPEND_DATA) or FILE_EXECUTE in the desired access mask. This ensures every fd has a valid `f_mode`:

- FILE_READ_DATA → FMODE_READ
- FILE_WRITE_DATA or FILE_APPEND_DATA → FMODE_WRITE
- FILE_EXECUTE (alone) → FMODE_EXEC

FMODE_EXEC enables `execveat(fd, "", ..., AT_EMPTY_PATH)` — an execute-only handle that cannot read or write file contents.

## Directories

Directory rights share bit positions with file data rights: FILE_LIST_DIRECTORY = FILE_READ_DATA (0x0001), FILE_ADD_FILE = FILE_WRITE_DATA (0x0002), FILE_ADD_SUBDIRECTORY = FILE_APPEND_DATA (0x0004). A native directory open with FILE_LIST_DIRECTORY satisfies the data-right requirement and maps to FMODE_READ.

## Special filesystem nodes

Existing FIFOs, pathname socket nodes, character device nodes, and block
device nodes on FACS-managed mounts are filesystem file objects for KACS
authorization. They use the file object type and the file-right mapping:
`FILE_READ_DATA` maps to `FMODE_READ`; `FILE_WRITE_DATA` or
`FILE_APPEND_DATA` maps to `FMODE_WRITE`; metadata, standard, and generic file
rights are evaluated with the file GenericMapping.

`FILE_EXECUTE` is not a valid native-open data substitute for these special
nodes. A `kacs_open` request that would open a FIFO, pathname socket node,
character device node, or block device node with `FILE_EXECUTE` fails closed.
The Linux object implementation may still impose additional device-specific
or filesystem-specific denial after KACS authorizes the file object.

Symlink objects are filesystem file objects for `kacs_get_sd`, `kacs_set_sd`,
and `readlink` authorization. They are not opened as terminal objects by
`kacs_open`: following is the default path-resolution behavior, and
`AT_SYMLINK_NOFOLLOW` fails with `-ELOOP`.

## Metadata-only operations

Operations that need no data or execute access (e.g., changing a file's DACL without reading its contents) use path-based interfaces or O_PATH fds as object anchors. The KACS get/set-security syscalls accept O_PATH fds via AT_EMPTY_PATH.

`AT_SYMLINK_NOFOLLOW` on `kacs_open` uses normal open semantics: the terminal
symlink is not opened and the call fails with `-ELOOP`. This differs from
`kacs_get_sd` / `kacs_set_sd`, where `AT_SYMLINK_NOFOLLOW` resolves the
symlink object itself.

## Create dispositions

| Value | Name | If exists | If doesn't exist |
|---|---|---|---|
| 0 | FILE_SUPERSEDE | Delete and recreate | Create |
| 1 | FILE_OPEN | Open | Fail |
| 2 | FILE_CREATE | Fail | Create |
| 3 | FILE_OPEN_IF | Open | Create |
| 4 | FILE_OVERWRITE | Truncate to zero | Fail |
| 5 | FILE_OVERWRITE_IF | Truncate to zero | Create |

FILE_SUPERSEDE deletes the existing file name and creates a new file with the
same name. Requires DELETE on the existing file (or FILE_DELETE_CHILD on the
parent) AND FILE_ADD_FILE on the parent. The new file gets a new inode and a
new SD (inherited from parent or caller-supplied). The superseded pathname is
broken away from the old hardlink set: that pathname names the new inode after
supersede. Other pre-existing hardlink pathnames to the old inode remain valid
and continue to name the old inode. Already-open fds reference the old inode.

FILE_OVERWRITE truncates the existing file to zero length. Same inode, same SD, hardlinks preserved. Requires FILE_WRITE_DATA.

### DELETE / FILE_DELETE_CHILD fallback during open

FILE_SUPERSEDE and DELETE_ON_CLOSE reference "DELETE on the file (or FILE_DELETE_CHILD on the parent)." This is a two-SD check within the open path. The kernel first runs AccessCheck against the target file's SD for DELETE. If DELETE is not granted, the kernel runs a second AccessCheck against the parent directory's SD for FILE_DELETE_CHILD. If neither check grants the required right, the open fails. This follows the same duality described in the link operation semantics.

FILE_DELETE_CHILD is a parent-directory authorization right for namespace
operations. It is not a cached native-open handle right in `v0.20`.
`kacs_open` MUST reject `desired_access` masks that contain FILE_DELETE_CHILD
with `-EOPNOTSUPP`.

## Create options

| Value | Name | Description |
|---|---|---|
| 0x0001 | KACS_CREATE_OPT_DIRECTORY | The target MUST be a directory. If creating, create a directory instead of a regular file. If opening an existing non-directory, fail with `-ENOTDIR`. |
| 0x0002 | KACS_CREATE_OPT_DELETE_ON_CLOSE | Delete the file when the last handle to it is closed. Requires DELETE on the file (or FILE_DELETE_CHILD on the parent). The deletion occurs at handle close, not at last-reference drop. |

All other bits are reserved and MUST be zero. The kernel rejects non-zero reserved bits with `-EINVAL`.

The slow-track mapping for `KACS_CREATE_OPT_DELETE_ON_CLOSE` is intentionally
no-share. `kacs_open_how` has no share-mode field, so the Windows
`FILE_SHARE_DELETE` compatibility matrix is not representable in the frozen
ABI. The bounded kernel contract is therefore:

- the delete-on-close obligation attaches to one ordinary file-description
  lineage, not to Linux inode last-reference semantics;
- `dup()`, `fork()`, `SCM_RIGHTS`, and similar fd transfers preserve that same
  obligation because they preserve the same open file description;
- once a delete-on-close lineage exists for a file object, later opens of that
  same object fail closed rather than emulating share-mode compatibility;
- the kernel performs the unlink at final close of that lineage, not at open
  time and not at generic inode last-reference drop;
- if the pathname is already gone by the time the final-close delete runs, the
  close path treats that as a no-op rather than a new error path.

The bounded slow-track implementation supports regular files only. Directory
delete-on-close remains out of scope and fails closed.

## Caller-supplied SD for creation

When a create disposition results in a new file, the caller MAY supply an SD via the `kacs_open_how` struct. If the SD pointer is null (and sd_len is 0), the new file's SD is inherited from the parent directory per the inheritance algorithm.

If `FILE_OPEN_IF` resolves to an existing object, the caller-supplied SD fields
(`sd_ptr`, `sd_len`) MUST be treated as invalid input. The syscall fails with
`-EINVAL` rather than silently ignoring a creation-only SD on the open-existing
branch.

If `FILE_OVERWRITE` or the existing-object branch of `FILE_OVERWRITE_IF`
resolves to an existing object, the caller-supplied SD fields (`sd_ptr`,
`sd_len`) MUST likewise be treated as invalid input. These dispositions retain
the existing inode and existing SD; creation-only SD input is therefore
invalid and the syscall fails with `-EINVAL`.

When a create disposition results in a new object, the kernel computes the
new object's SD first, then runs the normal strict native-open AccessCheck
against that new object's SD for the requested `desired_access`. Parent
create rights authorize namespace creation; they do not by themselves authorize
the returned handle. If the strict check on the new object fails, the creation
MUST be rolled back and the syscall fails.

Because `kacs_open_how` carries no POSIX mode field, the raw Linux inode mode
used for KACS-native creation is fixed:

- regular files are created with mode `0600`;
- directories are created with mode `0700`.

KACS-native creation does not create FIFOs, pathname socket nodes, character
device nodes, block device nodes, or symlinks. Special-node creation remains
on the Linux namespace APIs such as `mknod()` / `mkfifo()` / Unix
`bind()`-to-path, which are governed by the namespace hooks.

These mode bits are compatibility metadata only. If Linux DAC ever denies an
operation that KACS would otherwise authorize, the operation fails closed.

Creator-SD validation at create time follows these rules:

- if the creator SD specifies an owner, that SID MUST be the caller's own SID
  or a caller token group marked `SE_GROUP_OWNER`, unless
  `SeRestorePrivilege` is enabled, in which case any owner SID is allowed;
- if the creator SD supplies a SACL, it is treated as a full SACL input, not a
  label-only fragment, and therefore requires `SeSecurityPrivilege`;
- if that SACL contains an explicit mandatory-label ACE, the label MUST also
  satisfy the ordinary label-write constraint: without `SeRelabelPrivilege`,
  the requested label MUST be at or below the caller's integrity level.

## Creation status

The syscall MAY return a creation status indicating what happened: created, opened, overwritten, or superseded.

`KACS_STATUS_SUPERSEDED` is used only when an existing object is actually
replaced. If `FILE_SUPERSEDE` resolves to a missing target and creates a new
object without replacing an existing one, the reported status is
`KACS_STATUS_CREATED`.

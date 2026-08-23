---
title: KACS-Native Open
description: Opening a file by naming every right up front — the required data right, directories, special nodes, create dispositions and the DELETE fallback.
---

`kacs_open` takes an explicit desired access mask. The caller names
every right it will need — `FILE_READ_DATA`, `FILE_WRITE_DATA`,
`WRITE_DAC`, `READ_CONTROL`, any combination — and AccessCheck
evaluates the whole requested mask at open. If every requested right
is granted the descriptor's mask is set to the requested mask; if any
is denied, the open fails. This is the **strict** mode, in contrast to
the legacy path's subset behaviour (§3.9.3).

`MAXIMUM_ALLOWED` may be combined with at least one concrete data
right or `FILE_EXECUTE`. The concrete bits define the Linux `f_mode`
of the returned descriptor and have to be granted; `MAXIMUM_ALLOWED`
then makes the cached mask the full computed maximum rather than the
requested set. Alone it is invalid, because it defines no file mode,
and fails with `EINVAL`.

## The required data right

Every native open names at least one data right — `FILE_READ_DATA`,
`FILE_WRITE_DATA`, `FILE_APPEND_DATA` — or `FILE_EXECUTE`, so that
every descriptor has a valid mode. `FILE_READ_DATA` maps to
`FMODE_READ`; either write right maps to `FMODE_WRITE`; and
`FILE_EXECUTE` alone maps to `FMODE_EXEC`, which enables
`execveat(fd, "", ..., AT_EMPTY_PATH)` — an execute-only handle that
can neither read nor write the file's contents.

## Directories

Directory rights share bit positions with file data rights:
`FILE_LIST_DIRECTORY` is `FILE_READ_DATA` (0x0001), `FILE_ADD_FILE` is
`FILE_WRITE_DATA` (0x0002), and `FILE_ADD_SUBDIRECTORY` is
`FILE_APPEND_DATA` (0x0004). A native directory open with
`FILE_LIST_DIRECTORY` satisfies the data-right requirement and maps to
`FMODE_READ`.

The two write aliases are not cacheable directory handle rights,
though. `kacs_open` rejects a desired mask naming `FILE_ADD_FILE`,
`FILE_ADD_SUBDIRECTORY` or `FILE_DELETE_CHILD` on a directory with
`EOPNOTSUPP`. Those are parent-directory authorization rights for
namespace operations, evaluated live at the operation, not rights a
handle carries.

## Special nodes and symlinks

Existing FIFOs, pathname socket nodes, and character and block device
nodes on managed mounts are ordinary filesystem file objects for
authorization: the file object type, the file right mapping, and the
file GenericMapping for metadata, standard and generic rights.

`FILE_EXECUTE` is not a valid data substitute for them — a
`kacs_open` naming it on such a node fails closed. The Linux object
implementation may still impose its own device- or
filesystem-specific denial after KACS has authorized the file object.

Symlink objects are file objects for `kacs_get_sd`, `kacs_set_sd` and
`readlink`, but they are not opened as terminal objects by
`kacs_open`. Following is the default resolution behaviour, and
`AT_SYMLINK_NOFOLLOW` fails with `ELOOP`. This differs deliberately
from `kacs_get_sd` and `kacs_set_sd`, where the same flag resolves the
symlink object itself.

Operations needing neither data nor execute access — changing a
DACL without reading contents — use path-based interfaces or `O_PATH`
descriptors as object anchors, which the get and set security calls
accept through `AT_EMPTY_PATH`.

## Create dispositions

| Value | Name | If it exists | If it does not |
|---|---|---|---|
| 0 | `FILE_SUPERSEDE` | Delete and recreate | Create |
| 1 | `FILE_OPEN` | Open | Fail |
| 2 | `FILE_CREATE` | Fail | Create |
| 3 | `FILE_OPEN_IF` | Open | Create |
| 4 | `FILE_OVERWRITE` | Truncate to zero | Fail |
| 5 | `FILE_OVERWRITE_IF` | Truncate to zero | Create |

`FILE_SUPERSEDE` deletes the existing name and creates a new file
under it, requiring `DELETE` on the existing file — or
`FILE_DELETE_CHILD` on the parent — together with `FILE_ADD_FILE` on
the parent. The new file gets a new inode and a new descriptor,
inherited or caller-supplied. The superseded pathname is broken away
from the old hardlink set and names the new inode; other pre-existing
hardlinks continue to name the old inode, and already-open descriptors
still reference it.

`FILE_OVERWRITE` truncates in place — same inode, same descriptor,
hardlinks preserved — and requires `FILE_WRITE_DATA`.

On an `unmanaged` mount, `FILE_OPEN` and `FILE_OPEN_IF` succeed and
return an unmanaged descriptor with no stamped mask rather than
failing; the creating dispositions fail with `EOPNOTSUPP`.

### The DELETE fallback

Both `FILE_SUPERSEDE` and delete-on-close reference "`DELETE` on the
file, or `FILE_DELETE_CHILD` on the parent". That is a two-descriptor
check inside the open path: AccessCheck runs first against the target
file for `DELETE`, and if that is not granted it runs again against
the parent directory for `FILE_DELETE_CHILD`. If neither grants, the
open fails. The same duality governs link operations.

## Create options

| Value | Name | Description |
|---|---|---|
| 0x0001 | `KACS_CREATE_OPT_DIRECTORY` | The target has to be a directory. When creating, create a directory rather than a regular file; when opening an existing non-directory, fail with `ENOTDIR`. |
| 0x0002 | `KACS_CREATE_OPT_DELETE_ON_CLOSE` | Delete the file when the last handle in its lineage closes. Requires `DELETE` on the file or `FILE_DELETE_CHILD` on the parent. |

All other bits are reserved and have to be zero; a nonzero reserved
bit fails with `EINVAL`.

Delete-on-close is deliberately **no-share**. `kacs_open_how` carries
no share-mode field, so the Windows `FILE_SHARE_DELETE` compatibility
matrix is not representable in the frozen ABI, and the kernel contract
is bounded instead. The obligation attaches to one ordinary file
description lineage rather than to Linux inode last-reference
semantics, so `dup()`, `fork()` and `SCM_RIGHTS` all preserve it
because they preserve the description. Once a lineage exists for a
file object, later opens of that object fail closed rather than
emulating share-mode compatibility. The unlink happens at final close
of that lineage — not at open, and not at generic inode
last-reference drop — and if the pathname is already gone by then the
close path treats it as a no-op rather than a new error. Regular files
only: directory delete-on-close fails closed.

## Caller-supplied descriptors

When a disposition results in a new file the caller may supply a
descriptor. A null pointer with zero length means the new file's
descriptor is inherited from the parent directory through the
inheritance algorithm.

Supplying one on a branch that opens an *existing* object is invalid
input rather than something silently ignored. `FILE_OPEN_IF`
resolving to an existing object fails with `EINVAL`, and so do
`FILE_OVERWRITE` and the existing-object branch of
`FILE_OVERWRITE_IF`, since those retain the existing inode and its
descriptor. `FILE_OPEN` with a descriptor supplied fails with
`EOPNOTSUPP`.

For a genuine creation the kernel computes the new object's descriptor
**first**, then runs the strict native-open AccessCheck against *that*
descriptor for the requested access. Parent create rights authorize
namespace creation; they do not by themselves authorize the returned
handle. A failed strict check rolls the creation back — the newly
created file or directory is removed — and the syscall fails.

Creator-supplied descriptors are validated at create time. An owner
SID has to be the caller's own or a token group marked
`SE_GROUP_OWNER`, unless `SeRestorePrivilege` is enabled, in which
case any owner is allowed. A supplied SACL is treated as a full SACL
input rather than a label-only fragment, and therefore requires
`SeSecurityPrivilege`. If that SACL carries an explicit mandatory
label ACE, the label also has to satisfy the ordinary label-write
constraint: at or below the caller's integrity level, unless
`SeRelabelPrivilege` is held.

## Modes and status

`kacs_open_how` carries no POSIX mode field, so the raw Linux inode
mode for native creation is fixed: `0600` for regular files, `0700`
for directories. These are compatibility metadata only — and if Linux
DAC ever denies an operation KACS would have authorized, the operation
fails closed.

Native creation does not create FIFOs, socket nodes, device nodes or
symlinks. Those stay on the Linux namespace APIs — `mknod()`,
`mkfifo()`, Unix `bind()` to a path — governed by the namespace hooks.
NTFS is excluded from native creation entirely.

The syscall reports what happened: created, opened, overwritten, or
superseded. `KACS_STATUS_SUPERSEDED` is used only when an existing
object was actually replaced — a `FILE_SUPERSEDE` that finds no target
and simply creates one reports `KACS_STATUS_CREATED`.

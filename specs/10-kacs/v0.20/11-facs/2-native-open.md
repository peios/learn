---
title: KACS-Native Open
---

Peios provides a KACS-native open syscall that takes an explicit desired access mask. The caller names every right it will need: FILE_READ_DATA, FILE_WRITE_DATA, WRITE_DAC, READ_CONTROL, or any combination. AccessCheck evaluates the full requested mask at open time. If every requested right is granted, the fd's granted mask is set to the requested mask. If any requested right is denied, the open fails.

## Required data right

The KACS-native open MUST require at least one data right (FILE_READ_DATA, FILE_WRITE_DATA, FILE_APPEND_DATA) or FILE_EXECUTE in the desired access mask. This ensures every fd has a valid `f_mode`:

- FILE_READ_DATA → FMODE_READ
- FILE_WRITE_DATA or FILE_APPEND_DATA → FMODE_WRITE
- FILE_EXECUTE (alone) → FMODE_EXEC

FMODE_EXEC enables `execveat(fd, "", ..., AT_EMPTY_PATH)` — an execute-only handle that cannot read or write file contents.

## Directories

Directory rights share bit positions with file data rights: FILE_LIST_DIRECTORY = FILE_READ_DATA (0x0001), FILE_ADD_FILE = FILE_WRITE_DATA (0x0002), FILE_ADD_SUBDIRECTORY = FILE_APPEND_DATA (0x0004). A native directory open with FILE_LIST_DIRECTORY satisfies the data-right requirement and maps to FMODE_READ.

## Metadata-only operations

Operations that need no data or execute access (e.g., changing a file's DACL without reading its contents) use path-based interfaces or O_PATH fds as object anchors. The KACS get/set-security syscalls accept O_PATH fds via AT_EMPTY_PATH.

## Create dispositions

| Value | Name | If exists | If doesn't exist |
|---|---|---|---|
| 0 | FILE_SUPERSEDE | Delete and recreate | Create |
| 1 | FILE_OPEN | Open | Fail |
| 2 | FILE_CREATE | Fail | Create |
| 3 | FILE_OPEN_IF | Open | Create |
| 4 | FILE_OVERWRITE | Truncate to zero | Fail |
| 5 | FILE_OVERWRITE_IF | Truncate to zero | Create |

FILE_SUPERSEDE deletes the existing file and creates a new one with the same name. Requires DELETE on the existing file (or FILE_DELETE_CHILD on the parent) AND FILE_ADD_FILE on the parent. The new file gets a new inode and a new SD (inherited from parent or caller-supplied). Old hardlinks are broken. Already-open fds reference the old (now unlinked) inode.

FILE_OVERWRITE truncates the existing file to zero length. Same inode, same SD, hardlinks preserved. Requires FILE_WRITE_DATA.

## Create options

| Value | Name | Description |
|---|---|---|
| 0x0001 | KACS_CREATE_OPT_DIRECTORY | The target MUST be a directory. If creating, create a directory instead of a regular file. If opening an existing non-directory, fail with `-ENOTDIR`. |
| 0x0002 | KACS_CREATE_OPT_DELETE_ON_CLOSE | Delete the file when the last handle to it is closed. Requires DELETE on the file (or FILE_DELETE_CHILD on the parent). The deletion occurs at handle close, not at last-reference drop. |

All other bits are reserved and MUST be zero. The kernel rejects non-zero reserved bits with `-EINVAL`.

## Caller-supplied SD for creation

When a create disposition results in a new file, the caller MAY supply an SD via the `kacs_open_how` struct. If the SD pointer is null (and sd_len is 0), the new file's SD is inherited from the parent directory per the inheritance algorithm.

## Creation status

The syscall MAY return a creation status indicating what happened: created, opened, overwritten, or superseded.

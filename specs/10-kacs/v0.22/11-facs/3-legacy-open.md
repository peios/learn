---
title: Legacy Open Compatibility
---

Linux's `open()` / `openat()` cannot express rights like WRITE_DAC or READ_CONTROL. FACS maps open flags to a **core** set of required rights plus a **compat** set of POSIX-expected rights, then evaluates both in a single AccessCheck call.

## Core rights

Minimum rights for a usable legacy fd. The open MUST fail if any core right is denied.

For regular files, device nodes, FIFOs, and pathname sockets:

| Flags | Core rights |
|---|---|
| O_RDONLY | FILE_READ_DATA \| FILE_READ_ATTRIBUTES |
| O_WRONLY | FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES |
| O_RDWR | FILE_READ_DATA \| FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES |

For directories:

| Flags | Core rights |
|---|---|
| O_RDONLY | FILE_READ_ATTRIBUTES \| FILE_TRAVERSE |

Directory core does NOT include FILE_LIST_DIRECTORY. A directory opened O_RDONLY MAY be used for `fchdir()` and `fstat()` without requiring listing permission. FILE_LIST_DIRECTORY is in the compat set.

Modifiers (applied in order):

| Flag | Effect |
|---|---|
| O_APPEND | Replace FILE_WRITE_DATA with FILE_APPEND_DATA in core. |
| O_TRUNC | Add FILE_WRITE_DATA to core. |

When both O_APPEND and O_TRUNC are specified, both modifiers apply: FILE_WRITE_DATA is first replaced with FILE_APPEND_DATA (O_APPEND), then FILE_WRITE_DATA is re-added (O_TRUNC). The result is both FILE_APPEND_DATA and FILE_WRITE_DATA in core.

FILE_READ_ATTRIBUTES is always core. An SD that grants data access but denies attribute reads is not openable through legacy APIs.

## Compat rights

Requested alongside core — silently omitted if denied:

- FILE_READ_EA — `fgetxattr()`.
- READ_CONTROL — reading the SD.
- FILE_WRITE_ATTRIBUTES — `futimens()`.
- FILE_WRITE_EA — `fsetxattr()`.
- FILE_WRITE_DATA — included for O_APPEND opens so `ftruncate()` works if the SD allows it.
- WRITE_DAC — POSIX allows `fchmod()` on any fd.
- WRITE_OWNER — POSIX allows `fchown()` on any fd.
- SYNCHRONIZE.
- FILE_LIST_DIRECTORY — enables `readdir()` on directory fds.
- FILE_EXECUTE — enables `fexecve()` on regular file fds.

## The open-time flow

1. Construct the full requested mask: core | compat.
2. Run AccessCheck. AccessCheck returns a granted mask — the subset of requested rights the SD allows.
3. Check: are all core rights in the granted mask? If not, fail with EACCES.
4. Stamp the actual granted mask on the fd. This MAY include all, some, or none of the compat rights.

The two open paths use the same AccessCheck pipeline with different success criteria. KACS-native open: strict mode (`granted & requested == requested`). Legacy open: subset mode (insist only that core is fully present).

## O_PATH semantics

O_PATH fds are not FACS-managed. `security_file_open` does not fire for them. They carry no granted mask and serve as namespace anchors for `*at()` syscalls.

- `fstat()` / `fstatfs()` — allowed unconditionally.
- `fchdir()` — runs AccessCheck for FILE_TRAVERSE at use time.
- `fchmod()`, `fchown()`, `fgetxattr()`, `fsetxattr()`, `ioctl()`, `mmap()` — denied (EBADF).
- `execveat(fd, "", ..., AT_EMPTY_PATH)` — exec permission enforced via live AccessCheck in the bprm hook.
- `kacs_get_sd` / `kacs_set_sd` with AT_EMPTY_PATH — live AccessCheck against the file's SD. Provides race-free object identity without snapshot authorization.

> [!INFORMATIVE]
> O_PATH fds allow `fstat()` unconditionally, regardless of the SD. FILE_READ_ATTRIBUTES is therefore not authoritative for attribute confidentiality. In practice, file attributes (size, timestamps, inode number) are rarely confidential. The SD itself IS protected — `kacs_get_sd` on O_PATH performs a live AccessCheck.

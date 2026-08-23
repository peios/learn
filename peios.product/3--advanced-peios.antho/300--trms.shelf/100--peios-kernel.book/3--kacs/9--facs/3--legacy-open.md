---
title: Legacy Open Compatibility
description: Linux open flags cannot express WRITE_DAC or READ_CONTROL — how FACS maps them to core and compat rights, and what O_PATH does.
---

Linux's `open()` and `openat()` cannot express rights like `WRITE_DAC`
or `READ_CONTROL`. FACS maps the open flags to a **core** set of
required rights plus a **compat** set of POSIX-expected ones, and
evaluates both in a single AccessCheck.

## Core rights

The core set is the minimum for a usable descriptor, and the open
fails if any of it is denied.

For regular files, device nodes, FIFOs and pathname sockets:

| Flags | Core rights |
|---|---|
| `O_RDONLY` | `FILE_READ_DATA \| FILE_READ_ATTRIBUTES` |
| `O_WRONLY` | `FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES` |
| `O_RDWR` | `FILE_READ_DATA \| FILE_WRITE_DATA \| FILE_READ_ATTRIBUTES` |

For directories, `O_RDONLY` gives
`FILE_READ_ATTRIBUTES | FILE_TRAVERSE`. Directory core deliberately
excludes `FILE_LIST_DIRECTORY`, so a directory opened `O_RDONLY` can
be used for `fchdir()` and `fstat()` without listing permission;
listing is a compat right.

Two modifiers apply in order. `O_APPEND` replaces `FILE_WRITE_DATA`
with `FILE_APPEND_DATA`, and `O_TRUNC` adds `FILE_WRITE_DATA`. Given
both, the replacement happens first and the re-addition second, so
core ends up with `FILE_APPEND_DATA` and `FILE_WRITE_DATA` together.

`FILE_READ_ATTRIBUTES` is always core: a descriptor granting data
access but denying attribute reads is not openable through the legacy
APIs at all.

## Compat rights

Requested alongside core and silently omitted where denied:
`FILE_READ_EA` for `fgetxattr()`; `READ_CONTROL` for reading the
descriptor; `FILE_WRITE_ATTRIBUTES` for `futimens()`; `FILE_WRITE_EA`
for `fsetxattr()`; `FILE_WRITE_DATA` on `O_APPEND` opens so
`ftruncate()` works where the descriptor allows it; `WRITE_DAC`,
because POSIX permits `fchmod()` on any descriptor; `WRITE_OWNER`, for
`fchown()` on the same grounds; `SYNCHRONIZE`;
`FILE_LIST_DIRECTORY`, enabling `readdir()` on directory descriptors;
and `FILE_EXECUTE`, enabling `fexecve()` on regular files.

## The flow

The full requested mask is core plus compat. AccessCheck returns the
subset the descriptor allows. If every core right is present the
actual granted mask — which may include all, some or none of compat —
is stamped on the descriptor; otherwise the open fails with `EACCES`.

Both open paths run the same pipeline with different success
criteria. Native open is **strict**: everything requested has to be
granted. Legacy open is **subset**: only core has to be fully present.

## O_PATH

`O_PATH` descriptors are not FACS-managed. The open hook does fire for
them, but returns immediately without evaluating anything, so they
carry no granted mask and are left unmanaged. They serve as namespace
anchors for the `*at()` syscalls.

`fstat()` and `fstatfs()` on them are allowed unconditionally.
`fchdir()` runs a live `FILE_TRAVERSE` check at use time. `fchmod()`,
`fchown()`, `fgetxattr()`, `fsetxattr()`, `ioctl()` and `mmap()` are
denied with `EBADF` — though `futimens()` currently has no such guard.
`execveat(fd, "", ..., AT_EMPTY_PATH)` has exec permission enforced by
a live AccessCheck in the bprm hook, and `kacs_get_sd` and
`kacs_set_sd` with `AT_EMPTY_PATH` likewise run live, which gives
race-free object identity without snapshot authorization.

That `fstat()` is unconditional means `FILE_READ_ATTRIBUTES` is not
authoritative for attribute confidentiality. In practice size,
timestamps and inode number are rarely confidential. The descriptor
itself *is* protected: `kacs_get_sd` on an `O_PATH` handle performs a
live check.

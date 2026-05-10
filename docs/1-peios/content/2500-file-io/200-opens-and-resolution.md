---
title: Opens and Path Resolution
type: concept
description: The open syscall family on Peios — open/openat/openat2, the RESOLVE_* flags, O_* flag semantics, and recommendations for sandboxing path resolution.
related:
  - peios/file-io/overview-and-design
  - peios/file-io/io-operations
  - peios/access-control/check-at-open-model
  - peios/access-control/file-access-rights-reference
---

This page covers the Linux-legacy open paths and modern path-resolution controls. The KACS-native open is documented in the access-control section — see [Check-at-open model](../access-control/check-at-open-model).

## The open family

| Syscall | Purpose |
|---|---|
| `open(path, flags, mode)` | Open `path`, resolved against the calling process's CWD |
| `openat(dirfd, path, flags, mode)` | Open `path`, resolved against `dirfd` (or CWD if `AT_FDCWD`) |
| `openat2(dirfd, path, &how, sizeof(how))` | Open with extended `struct open_how` — flags + resolve flags + extensible |

All three resolve into the same AccessCheck pipeline. The flags map to KACS access masks via the legacy-open compatibility table — see [Check-at-open model](../access-control/check-at-open-model) for the precise mapping.

`openat2` is the modern interface. It accepts a `struct open_how` whose size is passed explicitly, enabling forward-compatible additions, and supports the **RESOLVE flags** for sandboxed path resolution (see below).

## Open flags (`O_*`)

Standard Linux open flags are honoured. The flag determines the requested access pattern, which the FACS legacy-open mapping translates into a core+compat access mask.

| Flag | Effect |
|---|---|
| `O_RDONLY` / `O_WRONLY` / `O_RDWR` | Access mode (mutually exclusive) |
| `O_CREAT` | Create if absent (requires FILE_ADD_FILE on parent) |
| `O_EXCL` | Fail if file already exists (with `O_CREAT`) |
| `O_TRUNC` | Truncate to zero length (adds FILE_WRITE_DATA to core) |
| `O_APPEND` | Append-only writes (replaces FILE_WRITE_DATA with FILE_APPEND_DATA in core) |
| `O_CLOEXEC` | Set FD_CLOEXEC on the resulting fd |
| `O_NONBLOCK` | Non-blocking I/O |
| `O_DIRECT` | Bypass the page cache (filesystem-dependent; honoured where supported) |
| `O_SYNC` / `O_DSYNC` | Synchronous writes (data + metadata, or data only) |
| `O_NOFOLLOW` | Fail if the final path component is a symlink |
| `O_NOATIME` | Don't update access time (requires the calling principal to be the SD owner or `SeBackupPrivilege`) |
| `O_TMPFILE` | Create an unnamed temporary file in the directory; can later be linked via `linkat` |
| `O_PATH` | Path-only fd — no I/O permitted, used as a namespace anchor for `*at()` syscalls. Not FACS-managed (see below) |

`O_TMPFILE` requires FILE_ADD_FILE on the directory. The resulting file has no path entry; it is named only by its fd. Linking it later via `linkat(fd, "", AT_FDCWD, target, AT_EMPTY_PATH)` creates a directory entry and requires FILE_ADD_FILE on the target's parent.

`O_NOATIME` exists for backup tools and bulk-read workloads that don't want to perturb access times. The principal-or-privilege gate matches Linux semantics.

## O_PATH semantics

An `O_PATH` fd is a path reference, not an open file. It carries no granted mask and is **not FACS-managed**. The fd serves as a namespace anchor for `*at()` syscalls (`fstatat`, `linkat`, `unlinkat`, etc.) and for race-free path operations.

| Operation on O_PATH fd | Allowed? |
|---|---|
| `fstat`, `fstatfs` | Yes, unconditionally |
| `fchdir` | Yes, with live AccessCheck for FILE_TRAVERSE |
| `fchmod`, `fchown`, `fgetxattr`, `fsetxattr`, `ioctl`, `mmap` | No (`EBADF`) |
| `execveat(fd, "", ..., AT_EMPTY_PATH)` | Yes, with live AccessCheck for FILE_EXECUTE in the bprm hook |
| `kacs_get_sd` / `kacs_set_sd` with `AT_EMPTY_PATH` | Yes, with live AccessCheck against the file's SD |

O_PATH fds allow `fstat` regardless of the SD — file attributes (size, timestamps, inode number) are not treated as confidential. The SD itself is protected by a live AccessCheck on `kacs_get_sd`.

## RESOLVE flags

`openat2` accepts a set of `RESOLVE_*` flags in `struct open_how.resolve` that constrain path resolution. These are the **modern Linux mechanism for sandboxed path resolution** — they let a caller bound where path resolution may go, preventing classic symlink-based escapes.

| Flag | Constraint |
|---|---|
| `RESOLVE_BENEATH` | All path components must be **at or below** the starting directory. `..` traversal that would escape the start is rejected. Symlinks that resolve outside the start are rejected. |
| `RESOLVE_IN_ROOT` | The starting directory is treated as the filesystem root. Absolute paths and `..` traversal are interpreted relative to the start. Used by container-style sandboxes. |
| `RESOLVE_NO_SYMLINKS` | Reject any symlink encountered during resolution (final component or intermediate). |
| `RESOLVE_NO_MAGICLINKS` | Reject magic links in `/proc` (e.g. `/proc/self/fd/N`) during resolution. Prevents magic-link attacks where a process tricks a trusted caller into opening a different file than expected. |
| `RESOLVE_NO_XDEV` | Reject any traversal that crosses a mountpoint. Useful for "stay on this filesystem." |
| `RESOLVE_CACHED` | Only succeed if the path can be resolved entirely from the dentry cache without I/O. Useful for non-blocking probes. |

### Sandboxing recommendation

Code that opens user-controlled paths SHOULD use `openat2` with appropriate RESOLVE flags rather than `openat` followed by post-hoc validation. The classic vulnerability pattern — open a path, check its resolved location, use the file — is racy: an attacker can swap a symlink between the check and the use. RESOLVE flags eliminate the race by making path-resolution constraints part of the open itself.

The most useful flags for sandboxing:

- **`RESOLVE_BENEATH`** — for "open this file under this directory, never escape." Standard for unpacking archives, processing user uploads, container roots.
- **`RESOLVE_IN_ROOT`** — for "this directory is my filesystem root." Standard for chroot-style isolation without an actual chroot.
- **`RESOLVE_NO_SYMLINKS`** — when symlinks are unexpected and any of them indicates an attack.
- **`RESOLVE_NO_MAGICLINKS`** — for code that opens user-supplied paths and shouldn't be tricked by `/proc/self/fd/N` redirections.

These flags are **strongly recommended** for any service that opens paths derived from untrusted input. Peios's KACS-native open will accept the same RESOLVE flags via the `kacs_open_how` struct (via the `howsize`-extensible pattern).

## File descriptor manipulation

Operations on existing fds:

| Syscall / fcntl | Purpose |
|---|---|
| `close(fd)` | Close an fd. Drops the reference; if last reference, releases the open file description. |
| `close_range(low, high, flags)` | Close all fds in `[low, high]`. Used to prune fd inheritance before exec. |
| `dup(fd)` / `dup2(old, new)` / `dup3(old, new, flags)` | Duplicate an fd. The new fd refers to the same open file description with the same granted mask. |
| `fcntl(fd, F_DUPFD, min)` | Duplicate to lowest fd ≥ `min`. |
| `fcntl(fd, F_DUPFD_CLOEXEC, min)` | Same, with FD_CLOEXEC set. |
| `fcntl(fd, F_GETFD)` / `F_SETFD` | Read/set fd flags (FD_CLOEXEC). |
| `fcntl(fd, F_GETFL)` / `F_SETFL` | Read/set file status flags (O_NONBLOCK, O_APPEND, etc.). |

The granted mask cached on an fd is **immutable** through duplication. `dup` does not relax or tighten authority — it produces a second fd referring to the same open file description.

`close_range` is the modern bulk-close primitive. It is dramatically faster than the close-in-a-loop pattern and avoids races where intermediate fds open between iterations of a loop.

## Per-process FD limits

The per-process open-fd limit is `RLIMIT_NOFILE`. The system-wide limit is read from `/proc/sys/fs/file-max` and exposed via `/proc/sys/fs/file-nr`. See [Resource limits](resource-limits) for the registry knobs and DoS posture.

## Async I/O notification

`fcntl(fd, F_SETOWN, pid)` registers a process to receive `SIGIO` when the fd becomes ready for I/O. `F_SETOWN_EX` extends this to threads and process groups. `F_SETSIG` overrides the default `SIGIO` with a real-time signal that carries siginfo. These are honoured for Linux compatibility but largely superseded by epoll, signalfd, and io_uring.

## Procfs FD enumeration

The `/proc/[pid]/fd/` directory exposes a process's open fds as symbolic links to the underlying file. `/proc/[pid]/fdinfo/` exposes per-fd metadata (offset, flags, granted mask, lease state).

Access to another process's `/proc/[pid]/fd/` is gated by KACS via PIP — readable only if the calling principal has appropriate dominance over the target process. See [process security](../process-security) for PIP semantics.

## See also

- [Check-at-open model](../access-control/check-at-open-model) — the FACS handle model and how flag-to-mask mapping works.
- [File access rights reference](../access-control/file-access-rights-reference) — the FILE_* access mask bits.
- [I/O operations](io-operations) — what you can do with an fd once you have it.

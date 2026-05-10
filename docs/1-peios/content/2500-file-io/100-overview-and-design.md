---
title: File Descriptors and I/O — Overview and Design
type: concept
description: How Peios manages file descriptors and I/O operations, the two-tier authority model (KACS-native open and Linux-legacy open), and the relationship to FACS.
related:
  - peios/file-io/opens-and-resolution
  - peios/file-io/io-operations
  - peios/file-io/locking-and-leases
  - peios/file-io/notifications
  - peios/file-io/resource-limits
  - peios/access-control/check-at-open-model
---

The file descriptor — `fd`, an integer index into the process's open-file table — is the universal handle for kernel-mediated I/O on Peios as on Linux. A process opens a file (or pipe, socket, device, eventfd, signalfd, etc.), receives an fd, and uses that fd for subsequent operations until it is closed. The fd is the unit of authority: holding the fd is the right to use it.

This section covers the FD subsystem and the I/O operations layered on it. The authority model (when an open succeeds, what rights the resulting fd carries) lives in [Access control — check-at-open](../access-control/check-at-open-model). This page describes the wider FD/I/O surface and where each piece lives.

## Two open paths

Peios offers two interfaces for opening a file:

| Path | Caller declares | AccessCheck mode | Use |
|---|---|---|---|
| **KACS-native open** | Explicit access mask (FILE_READ_DATA, WRITE_DAC, etc.) | Strict — every requested right must be granted | Peios-aware applications |
| **Linux-legacy open** (`open`/`openat`/`openat2`) | Open flags (O_RDONLY, O_WRONLY, etc.) | Subset — core rights mandatory, compat rights opportunistic | Linux compatibility |

The kernel resolves both into the same AccessCheck pipeline against the file's security descriptor. The fd that comes out of either path carries a single immutable **granted mask** — the set of rights the SD allowed at open time. Subsequent operations on the fd are gated by checking the cached mask, not by re-running AccessCheck.

This is the **handle model**: authority is on the handle, not on the holder. Once an fd exists, it can be inherited via fork, duplicated via dup, transferred via SCM_RIGHTS or pidfd_getfd, and survive exec — the granted mask travels with it. See [check-at-open model](../access-control/check-at-open-model) for the full handle-model semantics.

## Linux compatibility

The standard Peios server build ships the full Linux FD/I/O surface intact:

- All Linux open variants (`open`, `openat`, `openat2`) and their flags (`O_*`)
- All `fcntl` operations (locks, leases, signal owner, sealing, file flags)
- All read/write variants (basic, positional, vectored, with flags)
- Zero-copy primitives (sendfile, splice, tee, vmsplice, copy_file_range)
- Space-management primitives (fallocate, ftruncate, sync family)
- Notification subsystems (inotify, fanotify, legacy dnotify)
- Lock subsystems (POSIX records, OFD, flock)
- AIO interfaces (POSIX AIO via libc, native AIO, io_uring)

These are the surfaces Linux applications call directly. A Linux binary running on Peios uses these the same way it would on Linux. Authority is enforced through FACS (the file-specific projection of KACS) — the Linux flags map to KACS access masks, and AccessCheck runs at every open.

## Threat model

The FD subsystem is the **primary syscall surface for file access**. Almost every interesting file operation a process performs flows through it. Three threat-model considerations shape the design:

1. **Open is the gate.** AccessCheck runs once at open time; the cached mask is the authority for subsequent operations. A process that has obtained an fd is assumed to be authorized for every right cached in the granted mask, even if the SD is later modified. This is the handle model and is shared with NT.
2. **fd transfer is intentional capability delegation.** SCM_RIGHTS, pidfd_getfd, and fork all transfer fds without re-running AccessCheck. Code that hands out fds is delegating authority.
3. **Notification subsystems can be a side channel and a DoS vector.** inotify and fanotify can leak metadata about files the watching process couldn't otherwise observe (e.g. existence, modification times). They also have resource limits that an attacker can exhaust. fanotify permission events go further — they let userspace gate file operations synchronously, which is a privilege escalation vector if the gating principal is compromised.

Each of these is addressed on its dedicated page.

## What lives on which page

| Topic | Page |
|---|---|
| `open`/`openat`/`openat2`, RESOLVE flags, path resolution, O_* flags | [Opens and resolution](opens-and-resolution) |
| Read/write family, vectored I/O, zero-copy, fallocate, sync, AIO posture | [I/O operations](io-operations) |
| POSIX locks, OFD locks, flock, file leases | [Locking and leases](locking-and-leases) |
| inotify, fanotify, dnotify, FS_PRE_ACCESS, permission events | [Notifications](notifications) |
| RLIMIT_NOFILE, file-max, inotify/fanotify limits, registry knobs | [Resource limits](resource-limits) |

## See also

- [Check-at-open model](../access-control/check-at-open-model) — the handle model that underpins FACS.
- [File access rights reference](../access-control/file-access-rights-reference) — the FILE_* access mask bits.
- [io_uring](../IPC/io-uring) — the modern kernel-async I/O interface, layered on the same FD model.

---
title: Locking and Leases
type: concept
description: File locking primitives on Peios — POSIX record locks, OFD locks, BSD flock, and file leases (with the SeManageFileLeasePrivilege gate).
related:
  - peios/file-io/overview-and-design
  - peios/file-io/notifications
  - peios/privileges/manage-file-lease
---

Peios honours all three Linux file-locking interfaces and the file-lease subsystem. This page covers each, the interactions between them, and the privilege model around leases.

## POSIX record locks (legacy)

POSIX record locks are advisory locks on byte ranges of a file, acquired through `fcntl(F_SETLK | F_SETLKW | F_GETLK, ...)`. They predate every other Linux locking interface and have well-known semantic quirks:

- **Process-scoped, not fd-scoped.** A single process holds at most one lock per byte range, regardless of how many fds it has open on the file.
- **Released on any close.** Closing **any** fd on the file releases the process's locks on that file, even if other fds remain open.
- **Not inherited across `fork`.** Child processes do not inherit the parent's locks.
- **Inherited across `exec`.** The process keeps its locks across `execve`.

These semantics are unergonomic — closing a library-internal fd can release locks the application is relying on. POSIX record locks are shipped for compatibility with applications that depend on them, but new code should prefer OFD locks (below) or `flock`.

## OFD locks (open file description locks)

OFD locks are the modern fix to POSIX record locks' process-scoped semantics. They are acquired via `fcntl(F_OFD_SETLK | F_OFD_SETLKW | F_OFD_GETLK, ...)` and have these properties:

- **Per-open-file-description, not per-process.** Two fds on the same file from different `open()` calls have independent OFD locks.
- **Released only when the open file description is released** — i.e., when the last fd referring to it is closed.
- **Inherited across `fork`** (the child shares the same open file description).
- **Inherited across `exec`** unless `O_CLOEXEC` is set.

OFD locks are wire-compatible with POSIX record locks — both kinds compete for the same lock state on the file. A POSIX lock and an OFD lock on the same byte range will block each other.

OFD locks are the **recommended** modern interface for byte-range locking on Peios.

## BSD flock

`flock(fd, op)` provides whole-file advisory locks with a simpler model than POSIX or OFD record locks:

- **Per-open-file-description.** `flock` is held on the open file description, like OFD locks.
- **Whole-file only** — no byte-range support.
- **Two modes:** shared (`LOCK_SH`) and exclusive (`LOCK_EX`).
- **Independent of POSIX/OFD locks** — `flock` and `fcntl` byte-range locks coexist without interference.

`flock` is the right choice when whole-file mutual exclusion is sufficient — much simpler than the byte-range interfaces.

## Locking is advisory

All three locking interfaces are **advisory**: they only constrain code that explicitly checks for or acquires locks. A process that does not consult the locking subsystem can read and write the file without restriction (subject only to the granted mask on its fd). This is unlike Windows' mandatory locking, which the kernel itself enforces against all I/O.

Mandatory locking is **not supported** on Peios. The Linux mandatory-locking feature was removed upstream (kernel 5.15+) due to long-standing race conditions, and Peios follows that removal. Code that needs strict exclusion must use SD-based access control (e.g. `WRITE_DAC` to lock down a file's DACL during a critical section) or coordinate cooperatively through advisory locks.

## File leases

A file lease is a notification mechanism: a process acquires a lease on a file, and the kernel notifies that process (via signal) when **another process** attempts an operation that would conflict with the lease. The lease holder has a configured time (`/proc/sys/fs/leases-lease-break-time`, default 45 seconds) to release the lease before the kernel forcibly breaks it and lets the conflicting operation proceed.

Leases are most familiar from Samba, which uses them to implement Windows-style oplocks (opportunistic locks) — a Samba server holds a lease on each file an SMB client has cached, releases it when notified that another client is accessing the file, and signals the SMB client to flush its cache.

| `F_SETLEASE` arg | Effect |
|---|---|
| `F_RDLCK` | Acquire a read lease (notified on any write or unlink) |
| `F_WRLCK` | Acquire a write lease (notified on any open) |
| `F_UNLCK` | Release the lease |

`F_GETLEASE` returns the current lease state on the fd.

### Privilege model — SeManageFileLeasePrivilege

Linux gates `F_SETLEASE` on `CAP_LEASE` **only when the calling principal is not the file's owner** — you can always lease a file you own.

Peios maps this to a new privilege:

| Privilege | Gates |
|---|---|
| `SeManageFileLeasePrivilege` | `F_SETLEASE` on a file where the calling principal is not the SD owner |

Default holders: none. Granted to the Samba service principal at install time. Self-owned leasing works without the privilege, matching Linux's semantics.

The privilege is necessary because Samba (and any service that brokers files on behalf of remote clients) needs to lease arbitrary files — including files it doesn't own — for cache coherency. Adding the principal to every file's DACL would be impractical.

### Lease break protocol

When a conflicting operation arrives:

1. The kernel pauses the conflicting operation and signals the lease holder (default `SIGIO`, configurable via `F_SETSIG`).
2. The lease holder has up to `lease-break-time` seconds to release the lease (`F_UNLCK`) — this typically means flushing cached state and downgrading the holder's view of the file.
3. If the lease is not released in time, the kernel forcibly breaks it and proceeds with the conflicting operation. The lease holder receives a `SIGIO` indicating forced break.
4. A broken lease cannot be re-acquired without releasing the fd and re-opening.

This protocol is critical for Samba — failure to respond promptly causes SMB clients to see stale file state. Peios honours the same timing semantics.

## Interaction with the handle model

Locks are tied to the open file description (or process, for legacy POSIX locks), not to the granted mask. A lock held by a process is independent of any subsequent SD modifications. The handle model applies — authority to acquire a lock is determined at open time (the fd must have appropriate access), and the lock persists for the life of the holder regardless of SD changes.

Cross-fd lock interactions follow the rules above:

- POSIX record locks compete across all fds in a process, including library-held fds.
- OFD locks are per-`open()` — independent across separate open file descriptions.
- `flock` is per-open-file-description — like OFD locks for whole-file scope.
- File leases are per-fd — held on the specific fd that called `F_SETLEASE`.

## See also

- [SeManageFileLeasePrivilege](../privileges/manage-file-lease) — the privilege that gates cross-owner file leases.
- [Notifications](notifications) — inotify and fanotify, the file-change-notification subsystems.
- [Check-at-open model](../access-control/check-at-open-model) — the handle model that locks build on.

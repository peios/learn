---
title: Filesystem Notifications
type: concept
description: The filesystem notification subsystems on Peios — inotify (per-path watch), fanotify (mount-wide and permission events with the SeFilterFileSystemPrivilege gate), legacy dnotify, and FS_PRE_ACCESS.
related:
  - peios/file-io/overview-and-design
  - peios/file-io/locking-and-leases
  - peios/file-io/resource-limits
  - peios/privileges/filter-filesystem
---

Peios honours three Linux filesystem-notification subsystems, layered by power and cost:

| Subsystem | Scope | Cost | Status |
|---|---|---|---|
| **inotify** | Per-watched-path. Read events from an fd. | Cheap, well-understood. | Recommended. |
| **fanotify** (observation) | Per-mount or per-filesystem. Per-pathname or by FID. | Moderate; may report on every file in a filesystem. | Recommended for system-wide observers. |
| **fanotify** (permission events) | Per-mount with synchronous gating of file operations. | Expensive — every gated operation pauses for userspace acknowledgement. | **Privileged** (`SeFilterFileSystemPrivilege`). |
| **dnotify** (`F_NOTIFY`) | Per-directory, signal-based, no event details. | Coarse and signal-driven. Legacy. | Shipped for compatibility. Discouraged. |

The line that matters: inotify and observation-mode fanotify are unprivileged (subject to the watcher having read access to the targets); permission-event fanotify and system-wide marks are privileged.

## inotify

`inotify_init1(flags)` creates an inotify instance — an fd that produces a stream of file-event records. `inotify_add_watch(inotify_fd, path, mask)` adds a watch on `path` with the events specified by `mask`. `inotify_rm_watch(inotify_fd, wd)` removes a watch.

Events are read from the inotify fd as a sequence of `struct inotify_event` records. Each carries the watch descriptor, an event mask, a cookie (used to pair `IN_MOVED_FROM` and `IN_MOVED_TO`), and the relative pathname for events on directory contents.

| Event | Meaning |
|---|---|
| `IN_ACCESS` / `IN_MODIFY` / `IN_ATTRIB` | File read / written / metadata changed |
| `IN_CLOSE_WRITE` / `IN_CLOSE_NOWRITE` | File closed (after a write or read-only) |
| `IN_OPEN` | File opened |
| `IN_MOVED_FROM` / `IN_MOVED_TO` | Directory entry moved (paired by cookie) |
| `IN_CREATE` / `IN_DELETE` | Directory entry created / removed |
| `IN_DELETE_SELF` / `IN_MOVE_SELF` | The watched path itself was deleted / moved |

Watch behaviour is modified by mask flags:

| Flag | Effect |
|---|---|
| `IN_ONLYDIR` | Fail if `path` is not a directory |
| `IN_DONT_FOLLOW` | Don't dereference a symlink at `path` |
| `IN_EXCL_UNLINK` | Don't deliver events for files that were unlinked but remain open elsewhere |
| `IN_MASK_ADD` | Add to an existing watch's mask rather than replacing |
| `IN_ONESHOT` | Remove the watch after the first event |

inotify is the workhorse interface for file-change watching. It is unprivileged — any principal that can `open` a path can watch it. Resource limits (`max_user_watches`, `max_user_instances`, `max_queued_events`) are documented in [Resource limits](resource-limits).

## fanotify

`fanotify_init(flags, event_fd_flags)` creates a fanotify instance. `fanotify_mark(fd, op, mask, dirfd, path)` adds, removes, or flushes marks. fanotify is more powerful than inotify in three ways:

1. **Mount and filesystem marks.** A single mark can cover an entire mount (`FAN_MARK_MOUNT`) or filesystem (`FAN_MARK_FILESYSTEM`), receiving events for every file on it.
2. **Permission events.** Marks can request synchronous notifications before specific operations complete; the watcher must respond `FAN_ALLOW` or `FAN_DENY`.
3. **Rich event identification.** Events can carry file identifiers (FIDs) that survive renames, mount-relative paths, target FIDs for renames, and pidfds for caller identification.

### Observation events

Standard observation events (no permission semantics):

| Event | Meaning |
|---|---|
| `FAN_ACCESS` / `FAN_MODIFY` / `FAN_ATTRIB` | File read / written / metadata changed |
| `FAN_CLOSE_WRITE` / `FAN_CLOSE_NOWRITE` | File closed (after a write or read-only) |
| `FAN_OPEN` / `FAN_OPEN_EXEC` | File opened (general / opened for execution) |
| `FAN_CREATE` / `FAN_DELETE` / `FAN_DELETE_SELF` | Directory entry created / deleted / self-deleted |
| `FAN_MOVED_FROM` / `FAN_MOVED_TO` / `FAN_RENAME` | Move / rename events |

Observation marks at inode scope (`FAN_MARK_INODE`) are unprivileged — the marker just needs read access to the target.

### Mark scope and privilege

| Mark scope | Flag | Privilege |
|---|---|---|
| Inode | `FAN_MARK_INODE` (default) | None (read access to the target) |
| Mount | `FAN_MARK_MOUNT` | `SeFilterFileSystemPrivilege` |
| Filesystem | `FAN_MARK_FILESYSTEM` | `SeFilterFileSystemPrivilege` |

Mount-wide and filesystem-wide marks observe **every file on the mount or filesystem**, including files the marker has no SD access to. This is a significant privilege — equivalent to "I can see every file operation on this volume" — so it is gated.

### Permission events

Permission events let a userspace daemon **synchronously gate** file operations. The kernel pauses the operation, delivers an event to the listener, and waits for a `FAN_ALLOW` or `FAN_DENY` response (with a configurable timeout — see fanotify watchdog below).

| Event | Operation gated |
|---|---|
| `FAN_OPEN_PERM` | An attempt to open a file |
| `FAN_ACCESS_PERM` | An attempt to read a file |
| `FAN_OPEN_EXEC_PERM` | An attempt to open a file for execution |

Use cases:

- **Antivirus scanners** — block opening a file until it has been scanned and is determined safe.
- **Cloud-content gateways** — populate a file from a remote source before the open completes.
- **Compliance/DLP** — block sensitive files based on classification at access time.

Permission events are the most powerful and most dangerous fanotify mode. A buggy or malicious permission-event listener can deny all file access on the watched scope, effectively bricking the system.

**`SeFilterFileSystemPrivilege`** is required for any fanotify_init that requests permission events.

There is no Windows user-mode analog — Windows handles this niche through filesystem **filter drivers** (kernel-mode minifilters), which are far more privileged. Peios's user-mode permission-event interface fills the same role at lower privilege than Linux's CAP_SYS_ADMIN gate, while remaining substantially privileged.

### Permission-event watchdog

Kernel 6.18 added a **watchdog** that detects unresponsive permission-event listeners. If a listener doesn't respond within a configured timeout, the kernel logs a diagnostic and may proceed with the operation rather than block indefinitely. This protects against permission-event listeners that hang or crash.

Peios honours the watchdog and exposes its timeout as a registry knob — see [Resource limits](resource-limits).

### File identification (FIDs)

Recent fanotify additions carry file-identification information that survives renames and works across containers:

| Flag | Effect |
|---|---|
| `FAN_REPORT_FID` | Each event carries a file handle identifying the affected file |
| `FAN_REPORT_DIR_FID` | Each event carries a directory file handle |
| `FAN_REPORT_NAME` | Each event carries the affected name (final component) |
| `FAN_REPORT_DFID_NAME` | Combined directory FID + name |
| `FAN_REPORT_TARGET_FID` | For rename/link events, the target FID (in addition to source) |
| `FAN_REPORT_PIDFD` | Each event carries a pidfd identifying the caller |

`FAN_REPORT_PIDFD` aligns with Peios's broader pidfd-based identification model — it lets a permission-event listener identify the caller in a way that survives PID reuse and integrates with KACS GUID-based identity (the pidfd resolves to the calling task's `process_guid`).

### FS_PRE_ACCESS

Kernel 6.14 added `FS_PRE_ACCESS` — a synchronous pre-access notification used by on-demand content systems (cloud-storage gateways that materialize files only when accessed). It is a permission-class event, gated by `SeFilterFileSystemPrivilege` like other permission events.

### Mount namespace notifications

Kernel 6.15 added fanotify support for observing mount-namespace operations. Useful for container-management tooling that wants to react to mount/unmount events.

### User-namespace awareness

Kernel 6.16 added user-namespace integration for fanotify. **Peios does not surface this** — Peios v1 rejects `CLONE_NEWUSER` (see [Process Silos](../process-silos/silos-and-namespaces)). The flag is honoured at the syscall level for ABI compatibility but has no effect.

### Generic fsnotify error reporting

Kernel 7.0 added a generic file-IO error reporting API via fsnotify — filesystems can surface metadata corruption and I/O error notifications through the notification framework rather than only through dmesg. This gives userspace a structured channel for filesystem-health monitoring.

## Legacy dnotify (F_NOTIFY)

`fcntl(fd, F_NOTIFY, mask)` is the original Linux directory-change notification interface, dating to kernel 2.4. It delivers events as `SIGIO` signals (or a configurable real-time signal via `F_SETSIG`) without details — the listener has to scan the directory itself to determine what changed.

dnotify has been superseded by inotify and fanotify in essentially every use case. It has well-known limitations:

- Signal-driven (not fd-readable) — interferes with applications that have other signal-handling needs
- No event details — listener must rescan
- Per-directory only — cannot watch individual files

Peios ships dnotify for compatibility with applications that still depend on it, but **new code should use inotify**. dnotify carries no privilege gate beyond the open-time access check on the directory.

## Choosing an interface

| Need | Use |
|---|---|
| Watch a small set of paths | **inotify** |
| Observe activity across an entire volume | **fanotify** with `FAN_MARK_MOUNT` (privileged) |
| Gate file operations from userspace | **fanotify** permission events (privileged) |
| Material on-demand content into a file before access | **fanotify** with FS_PRE_ACCESS (privileged) |
| Legacy applications | **dnotify** (only if porting impractical) |

## See also

- [SeFilterFileSystemPrivilege](../privileges/filter-filesystem) — the privilege that gates fanotify permission events and system-wide marks.
- [Resource limits](resource-limits) — registry knobs and DoS posture for inotify and fanotify.
- [Locking and leases](locking-and-leases) — file leases, the related mechanism for cache-coherency notifications.

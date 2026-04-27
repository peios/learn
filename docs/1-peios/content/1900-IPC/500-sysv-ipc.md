---
title: System V IPC
type: concept
description: System V IPC on Peios — semaphores, message queues, shared memory, and the security descriptor model that replaces the legacy ipc_perm 9-bit mode.
related:
  - peios/memory-management/shared-memory
  - peios/access-control/file-security-descriptors
  - peios/pip/understanding-pip
  - peios/privileges/se-lock-memory-privilege
---

System V IPC is the original Unix family of inter-process communication primitives — semaphores, message queues, and shared memory — defined originally in AT&T System V Release 2 in the mid-1980s. It is largely superseded by POSIX equivalents and modern primitives, but enough legacy software depends on it (PostgreSQL, Oracle, X11's MIT-SHM extension, older HPC code) that it remains part of the supported ABI.

This page covers the three SysV IPC kinds, their common security model, and how Peios maps the legacy `ipc_perm` 9-bit-mode infrastructure onto KACS security descriptors.

## The three kinds

| Kind | Created by | Used for |
|---|---|---|
| **Semaphores** | `semget(key, nsems, flags)` | Synchronisation. Each set holds N counters; `semop()` performs P/V operations on them with atomicity guarantees. |
| **Message queues** | `msgget(key, flags)` | Tagged-message passing between processes. Each message has a `mtype` long-integer tag; receivers can filter by tag. |
| **Shared memory** | `shmget(key, size, flags)` | Process-to-process shared memory segments. Mapped via `shmat()`, unmapped via `shmdt()`. |

All three share a common architecture: created in a kernel-internal table, identified by an integer ID returned from `*get()`, addressable by a user-supplied key (or `IPC_PRIVATE` for an unnamed object), persistent until explicitly destroyed via `*ctl(IPC_RMID)`. There is no filesystem presence beyond the read-only listing in `/proc/sysvipc/`.

## The Linux model — `ipc_perm`

On Linux, every SysV IPC object carries a `struct ipc_perm`:

```
struct ipc_perm {
    key_t key;       // user-supplied key
    uid_t uid;       // owner UID
    gid_t gid;       // owner GID
    uid_t cuid;      // creator UID
    gid_t cgid;      // creator GID
    mode_t mode;     // 9-bit rwx mode
    int seq;         // sequence number
};
```

Operations consult the `ipcperms()` function: owner gets the high three mode bits, group members the middle three, others the low three. Read-bit gates inspection (`semctl(GETVAL)`, `msgrcv`, `shmat` for read), write-bit gates state changes (`semop`, `msgsnd`, `shmat` for write). The execute bit is unused.

`ipc_perm.uid` and `gid` are owner UIDs (changeable via `IPC_SET`); `cuid` and `cgid` are creator UIDs (immutable). `IPC_RMID` (delete) requires owner UID match or `CAP_SYS_ADMIN`.

This is bare DAC — UID + group + others, no ACLs, no per-operation granularity beyond read/write. It mirrors filesystem permissions but on an object that has no filesystem entry.

## The Peios model — security descriptors

UIDs are projection artefacts on Peios; the legacy `ipc_perm` model cannot do the work it does on Linux. Instead, every SysV IPC object on Peios carries a full **security descriptor**, evaluated by the standard KACS AccessCheck path. The legacy `ipc_perm` fields are exposed via `IPC_STAT` for ABI compatibility but are computed from the SD, not the source of authority.

### Per-object-class access masks

Each IPC kind has its own access mask vocabulary, mirroring the operations possible on that kind:

**Shared memory** (already documented in [Shared Memory](../memory-management/shared-memory) but restated here for completeness):

| Mask | Operation |
|---|---|
| `SHM_READ` | `shmat()` for read access |
| `SHM_WRITE` | `shmat()` for write access |
| `SHM_ATTACH` | Permission to attach at all (precondition for `SHM_READ`/`SHM_WRITE`) |
| `SHM_CONTROL` | `shmctl()` operations beyond `IPC_STAT` |

**Semaphores:**

| Mask | Operation |
|---|---|
| `SEM_QUERY` | `semctl(GETVAL)`, `GETPID`, `GETNCNT`, `GETZCNT`, `GETALL` |
| `SEM_OP` | `semop()` / `semtimedop()` (P/V operations) |
| `SEM_CONTROL` | `semctl(SETVAL)`, `SETALL`, other state-set operations |

**Message queues:**

| Mask | Operation |
|---|---|
| `MSG_SEND` | `msgsnd()` |
| `MSG_RECV` | `msgrcv()` |
| `MSG_CONTROL` | `msgctl()` administrative ops beyond `IPC_STAT` |

**All three** also use the standard non-class-specific masks:

| Mask | Operation |
|---|---|
| `READ_CONTROL` | Read the SD itself (`*ctl(IPC_STAT)`) |
| `WRITE_DAC` | Modify the DACL (`*ctl(IPC_SET)` mode component) |
| `WRITE_OWNER` | Change the owner SID |
| `DELETE` | Destroy the object (`*ctl(IPC_RMID)`) |

The split between query/op/control on semaphores reflects the distinction between read-only inspection, value-affecting operations (which on Linux required write access), and parameter-affecting operations (`SETVAL`). This is finer-grained than Linux's two-bit (`R`/`W`) model and lets administrators grant operational permission without granting administrative permission — a valuable distinction for service architecture.

### Identity at create

When an IPC object is created via `*get(key, ..., flags | IPC_CREAT)`:

| Field | Source |
|---|---|
| Owner SID | Creator's effective token user SID |
| Group SID | Creator's effective token primary group SID |
| Initial DACL | Derived from the mode bits in `flags` (see below) |

The creator-SID linkage is symmetric with how filesystem objects pick up ownership at create time.

### Mode-to-DACL translation at create

The low 9 bits of `flags` to `*get()` traditionally specify a creation mode (`semget(key, 1, 0600 | IPC_CREAT)` creates with mode `0600`). On Peios, these bits map to an initial DACL using the standard 9-bit-mode-to-DACL translation:

| Linux mode | Peios initial DACL |
|---|---|
| `0600` | Owner full access, no one else. |
| `0660` | Owner full, group full, world none. |
| `0644` | Owner full, group read, world read. |
| `0666` | Owner full, group full, world full. |

The owner ACE grants the full per-object-class mask set (`SHM_READ` + `SHM_WRITE` + `SHM_ATTACH` + `SHM_CONTROL` for SHM, etc.) plus `READ_CONTROL`/`WRITE_DAC`/`WRITE_OWNER`/`DELETE`. Group and world ACEs grant the corresponding read/write subsets per the standard mode-to-DACL rules.

This mirrors how the same translation works for filesystem SDs at file creation. Software that currently uses `semget(0600)` to create owner-only IPC objects continues to produce owner-only objects on Peios; the SD just carries more granularity behind the scenes.

### IPC_SET — what it does on Peios

Linux `IPC_SET` writes uid, gid, and mode to the `ipc_perm`. On Peios:

- **Mode changes** map to DACL edits via the same 9-bit-to-DACL translation applied at create. Gated by `WRITE_DAC` on the SD. A successful `IPC_SET` with a new mode produces a new DACL reflecting the requested permissions.
- **uid and gid changes** are **rejected** with `EINVAL`. UID-to-SID reverse projection is ambiguous; multiple SIDs can project to the same UID. Linux software changing ownership via `IPC_SET` must instead use the Peios-native `kacs_set_security_descriptor` API on the IPC handle, which works directly in the SID space.

The rejection of uid/gid changes is a small compatibility break. The pragmatic impact is small — most software that uses `IPC_SET` is changing mode bits, not ownership, and the few cases that change ownership are typically administrative scripts that can be updated to use the native API.

### IPC_RMID — destruction

`*ctl(IPC_RMID)` requires the standard `DELETE` access mask on the SD. Default DACL grants `DELETE` to the owner. `WRITE_OWNER` can be used to transfer ownership without first deleting; the new owner can then `DELETE`.

A destroyed IPC object's SD is removed; subsequent attempts to access by the same key fail with `EIDRM` for processes still holding the old ID. `IPC_RMID` returns immediately even if processes are still attached (for SHM) or waiting (for sems/MQs); the actual cleanup happens when the last reference is released.

## /proc/sysvipc/ enumeration

`/proc/sysvipc/sem`, `/proc/sysvipc/msg`, and `/proc/sysvipc/shm` list the existing IPC objects. On Linux, anyone can list all objects of any kind, regardless of permissions. On Peios, the listing is **filtered per-object by `READ_CONTROL`**: a process sees only the IPC objects whose SD grants it `READ_CONTROL` (or higher). This matches the filtering pattern applied to `/proc/<pid>/` on Peios — you only see the objects you have inspection authority over.

The `ipcs(1)` userspace tool reads `/proc/sysvipc/` and so produces a filtered view automatically. Diagnostic tooling running with `SeTcbPrivilege` (or whose token grants `READ_CONTROL` on all relevant SDs) sees the full system listing.

## PIP enforcement

The standard `SYSTEM_PROCESS_TRUST_LABEL_ACE` mechanism applies to IPC object SDs. A low-PIP process operating on a higher-PIP-owned IPC object fails closed regardless of DACL. This is the same machinery as files; SysV IPC is not a special case.

In practice, this means a non-Protected process cannot `shmat` a Protected-process-owned SHM segment, cannot `semop` a Protected-process-owned semaphore, etc., even if the DACL would otherwise permit. PIP-aware code in the holder can still pass fds via `SCM_RIGHTS` to a lower-PIP recipient if that's the desired pattern, but the *object* itself remains PIP-locked.

## SHM_LOCK and the SeLockMemoryPrivilege gate

`shmctl(shmid, SHM_LOCK)` locks the SHM segment in physical RAM, preventing it from being paged out. This consumes locked-memory budget on the calling process and is gated by **`SeLockMemoryPrivilege`** plus the per-process locked-memory quota — the same mechanism that gates `mlock` of regular memory. See [Memory Locking](../memory-management/memory-locking) for the full model.

`SHM_UNLOCK` releases the lock. The lock is per-process: if multiple processes have locked the same SHM segment, the segment remains locked in RAM until all of them unlock. The locked-memory quota is charged per-locking-process.

## IPC limits

Kernel-wide limits on the number and size of IPC objects:

| Tunable | Purpose |
|---|---|
| `kernel.sem` | `(SEMMSL, SEMMNS, SEMOPM, SEMMNI)` — max sems per set, total sems, ops per call, total sem sets |
| `kernel.msgmax` / `msgmnb` / `msgmni` | Max message size, max queue size, max queues |
| `kernel.shmmax` / `shmall` / `shmmni` | Max SHM segment size, total SHM pages, max segments |

These are admin sysctls, registry-driven via ksyncd, gated by the registry key's SD. Default values are generous; they're tightened only on hardened images that deliberately constrain IPC usage, or raised on database hosts that need larger SHM segments.

## IPC namespace isolation

`CLONE_NEWIPC` creates a new IPC namespace, isolating its objects from the parent's namespace. A process in a different IPC namespace sees a fresh empty IPC table. The full namespace model and its interaction with KACS confinement is documented in the **Containerisation** category.

## Migration notes

Software porting from Linux to Peios mostly works unchanged. The points of friction are:

- **Authentication via UID**: software that consults `ipc_perm.uid` or `cuid` to identify creators gets projected UIDs, which are stable and useful for display but lossy for security decisions. For real authentication, use the SD directly (read via `*ctl(IPC_STAT)` or the native KACS API).
- **`IPC_SET` ownership changes**: applications that change uid/gid via `IPC_SET` will receive `EINVAL`. Workaround: use `kacs_set_security_descriptor` on the IPC handle.
- **Visibility filtering**: tools that walk `/proc/sysvipc/` and expect to see all objects on the system need either elevated authority or revised expectations.

## See also

- [Shared memory](../memory-management/shared-memory) — POSIX shared memory and `memfd`, the modern alternatives.
- [File security descriptors](../access-control/file-security-descriptors) — the SD model these IPC objects share.
- [Understanding PIP](../pip/understanding-pip) — the trust-label enforcement applied to IPC SDs.
- [Memory locking](../memory-management/memory-locking) — the privilege/quota model behind `SHM_LOCK`.

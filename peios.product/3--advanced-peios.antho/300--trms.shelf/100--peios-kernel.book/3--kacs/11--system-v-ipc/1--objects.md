---
title: Objects and Their Descriptors
description: Every System V message queue, shared memory segment and semaphore array carries a security descriptor, stamped at creation and enforced through the LSM IPC hooks.
---

System V IPC — message queues (`msgget`), shared memory segments
(`shmget`) and semaphore arrays (`semget`) — predates file descriptors
and paths: an object is named by an integer key, identified by an
integer id, and persists in the kernel until removed or reboot. Linux
protects each with a nine-bit mode in `struct ipc_perm`, checked by
`ipcperms()` against the caller's UID and GID.

On Peios that mode is inert. `CAP_IPC_OWNER` is in KACS's always-allow
set (§3.10.2), so `ipcperms()` never denies on the mode and always
reaches `security_ipc_permission()`; there KACS decides, against a
security descriptor the object carries.

## The descriptor

Each object gets a descriptor when it is created, built from the
creator's effective token: owner and group from the token; the
creator's user SID, `BUILTIN\Administrators` and `SYSTEM` at
`GENERIC_ALL`. It is held on the object's LSM blob for the object's
life — persisting with the object across the creator's exit, as SysV
objects do — and released when the object is removed.

The rights are those of `<pkm/ipc.h>`:

| Right | Grants |
|---|---|
| `KACS_IPC_READ` | `msgrcv`; `shmat` read-only; `semop` without alter; `GETVAL`, `GETPID`, `GETNCNT`, `GETZCNT`, `GETALL` |
| `KACS_IPC_WRITE` | `msgsnd`; `shmat` read-write; `semop` with alter; `SETVAL`, `SETALL` |
| `KACS_IPC_QUERY_INFORMATION` | `IPC_STAT` and the `SHM_STAT`, `MSG_STAT`, `SEM_STAT` families |
| `KACS_IPC_SET_INFORMATION` | `SHM_LOCK`, `SHM_UNLOCK` |
| `DELETE` | `IPC_RMID` |
| `WRITE_DAC` and `WRITE_OWNER` | `IPC_SET` — one command carries mode, uid and gid, so it needs both |
| `READ_CONTROL` | reading the descriptor with `kacs_get_sd` |

The generic mapping: `GENERIC_READ` is read plus query and
`READ_CONTROL`; `GENERIC_WRITE` is write plus set-information and
`READ_CONTROL`; `GENERIC_EXECUTE` is query and `READ_CONTROL`;
`GENERIC_ALL` is everything above.

## Where the checks run

`ipcperms()` runs for every data operation with the mode bits the
operation would have needed — read, write or both — and
`security_ipc_permission()` maps them to `KACS_IPC_READ` and
`KACS_IPC_WRITE` and runs AccessCheck for the caller's effective token,
under the caller's PIP context, against the object's descriptor. The
`*get` path with an existing key goes through the same check with the
requested mode. The control operations go through the per-object
`shmctl`, `msgctl` and `semctl` hooks, which map the command to the
right in the table above; commands that address no object
(`IPC_INFO`, `SHM_INFO`, `MSG_INFO`, `SEM_INFO`) need nothing.

Linux's own ownership check on `IPC_SET` and `IPC_RMID` — that the
caller's effective UID matches the object's creator or owner, or holds
`CAP_SYS_ADMIN` — still runs first, on the projected UID, and cannot be
relaxed by the descriptor: the hooks only ever further restrict. So an
administrator who is not the object's creator needs both the
descriptor's `DELETE` (which the default grants Administrators) and
`SeTcbPrivilege` (what `CAP_SYS_ADMIN` maps to) to remove it. The
`uid`, `gid` and `mode` that `IPC_SET` writes remain as Linux stores
them and are what `ipcs` and `IPC_STAT` report; they are informational,
as file mode bits are under FACS.

## Reading and changing a descriptor

A SysV object has no fd and no path, so `kacs_get_sd` and `kacs_set_sd`
address it by kind and id: one of `KACS_SD_AT_SYSV_SHM`,
`KACS_SD_AT_SYSV_MSG` or `KACS_SD_AT_SYSV_SEM` in `flags`, the object
id in `dirfd`, and a NULL path. The object is looked up in the caller's
IPC namespace; an unknown id is `EINVAL` and a removed one `EIDRM`.
Reading needs the rights the requested `SECURITY_INFORMATION` implies
(`READ_CONTROL` for owner, group and DACL; `ACCESS_SYSTEM_SECURITY`
for the SACL), changing needs `WRITE_DAC` or `WRITE_OWNER` as for any
object, and the new descriptor is merged into the existing one
component by component, as for a process descriptor (§3.3.3).

## Names

The key namespace is claim-on-create: whoever calls `*get` with
`IPC_CREAT` on a free key owns the object, and nothing prevents a
process from claiming a key another program expected to create — the
same shape as the abstract socket namespace and `/dev/shm`. The
descriptor protects the object once it exists; it cannot protect the
name. A program that needs a specific key uses `IPC_EXCL` and treats a
failure as a signal, and a program that needs identity-carrying
messaging uses an `AF_UNIX` socket (§3.5): a message queue conveys no
sender identity, and `msgrcv` returns bytes and a type, nothing more.

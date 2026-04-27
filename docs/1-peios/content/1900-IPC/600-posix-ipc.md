---
title: POSIX IPC
type: concept
description: POSIX IPC primitives on Peios — POSIX semaphores, POSIX message queues, and how they inherit access control from their backing filesystems.
related:
  - peios/IPC/sysv-ipc
  - peios/memory-management/shared-memory
  - peios/access-control/file-security-descriptors
---

POSIX IPC is the modern alternative to System V IPC, defined in the POSIX.1b real-time extensions. It covers semaphores, message queues, and shared memory, with cleaner semantics and (importantly for Peios) a more sensible access-control story: every POSIX IPC object has a filesystem presence, and access is gated by standard filesystem security descriptors.

This page covers POSIX semaphores and message queues. POSIX shared memory (`shm_open`) is documented in [Shared Memory](../memory-management/shared-memory) — it lives in the memory-management category because the dominant questions about it are memory-management questions.

## POSIX semaphores

POSIX semaphores have two flavours: **named** and **unnamed**.

### Named semaphores

Named semaphores live in tmpfs at `/dev/shm/sem.<name>`. Created with `sem_open()`:

```c
sem_t *sem = sem_open("/myservice", O_CREAT | O_EXCL, 0600, 1);
```

The name is a path-like string starting with a slash. Behind the scenes, the libc wrapper opens (or creates) a file at `/dev/shm/sem.myservice`. The kernel maps the file into both processes' address spaces and treats it as a semaphore primitive.

Operations:

| Call | Purpose |
|---|---|
| `sem_wait(sem)` / `sem_trywait(sem)` / `sem_timedwait(sem)` | Decrement (P operation). Block if value would go negative; trywait returns immediately; timedwait blocks with a deadline. |
| `sem_post(sem)` | Increment (V operation). |
| `sem_close(sem)` | Release the local handle without destroying the semaphore. |
| `sem_unlink(name)` | Remove the name. The semaphore lives until all processes close it. |

**Access control.** The SD on `/dev/shm/sem.<name>` gates access. `sem_open` for read+write requires `READ_DATA` and `WRITE_DATA`; subsequent `sem_wait`/`sem_post` use the file's protection of the existing fd. The `mode` argument to `sem_open(O_CREAT)` maps to the initial DACL via the standard 9-bit-mode-to-DACL translation, exactly as for any other file.

This is the model's strength: there's no separate "POSIX semaphore permission" surface to learn. It's a file in tmpfs, and standard tooling (`ls -l /dev/shm/`, `chmod`, `chown`-equivalent via the KACS native API) works on it.

### Unnamed (process-shared) semaphores

`sem_init(sem, pshared, value)` initialises a semaphore in a memory location the caller provides. The location may be in private memory (`pshared = 0`, the semaphore is per-process) or in a shared mapping (`pshared = 1`, e.g. memory created via `shm_open` or `mmap(MAP_SHARED)`).

Unnamed shared semaphores have **no separate access control** — access is governed by access to the surrounding shared memory. If two processes can both `mmap` the underlying SHM region, they can both use the semaphore embedded in it. The shared memory's SD is the gate.

`sem_destroy(sem)` releases an unnamed semaphore. There is no `sem_unlink` analogue.

## POSIX message queues

POSIX message queues live in their own filesystem, **mqueue**, conventionally mounted at `/dev/mqueue`. Each queue is a file in this filesystem; the file's SD gates access.

| Call | Purpose |
|---|---|
| `mq_open(name, oflag, mode, attr)` | Create or open a queue. Name is a slash-prefixed string; behind the scenes opens `/dev/mqueue/<name>`. |
| `mq_close(mq)` | Release the local handle. |
| `mq_unlink(name)` | Remove the queue. Existing handles remain valid until closed. |
| `mq_send(mq, msg, len, prio)` / `mq_timedsend(...)` | Send a message with a priority value. |
| `mq_receive(mq, buf, len, &prio)` / `mq_timedreceive(...)` | Receive the highest-priority message. |
| `mq_notify(mq, sigevent)` | Register a signal or thread to be notified when a message arrives on an empty queue. |
| `mq_getattr(mq, &attr)` / `mq_setattr(mq, ...)` | Query or modify queue attributes. |

POSIX message queues differ from System V message queues in two important ways:

- **Priorities, not type tags.** Each message carries a priority (0–32 by default). `mq_receive` always returns the highest-priority message available. There's no equivalent to System V's `mtype` filtering — receivers cannot select a specific message type.
- **Asynchronous notification.** `mq_notify` registers an asynchronous notification (a signal or a thread spawn) that fires when the queue transitions from empty to non-empty. System V has no analogous mechanism.

**Access control.** Mqueue files have full SDs, like any other file. `mq_open` for sending requires `WRITE_DATA`; for receiving, `READ_DATA`. The `mode` argument to `mq_open(O_CREAT)` maps to the initial DACL via the standard translation. `mq_setattr` requires `WRITE_DAC` on the SD if it changes attributes affecting access; otherwise just an open writable handle.

Limits on queue size, message size, and total queues per process live under `/proc/sys/fs/mqueue/`, registry-driven via ksyncd.

## Why POSIX IPC is the preferred path

Three reasons to prefer POSIX IPC over System V on Peios for new code:

**Filesystem-native access control.** Every POSIX IPC primitive has a corresponding file with a real SD. There's no need to learn a separate permission model, and standard SD-management tooling works.

**Sane defaults.** POSIX IPC primitives respect the standard filesystem security model — including PIP enforcement via the trust-label ACE, which applies because they're files. System V IPC's per-class access mask vocabulary requires understanding three different sets of operation names.

**Cleaner cleanup.** POSIX IPC lifetimes are tied to filesystem entries; `unlink` is the standard cleanup primitive, and the kernel handles the "wait for all closes" semantics naturally. System V IPC's `IPC_RMID` and the dance around persistent kernel-table entries is more error-prone.

The continuing case for System V IPC is **legacy software**: PostgreSQL's startup-collision detection, Oracle's SGA, X11's MIT-SHM, certain HPC frameworks. New code on Peios should use POSIX IPC unless there's a specific reason not to.

## See also

- [System V IPC](sysv-ipc) — the legacy alternative, with the per-class access mask model.
- [Shared memory](../memory-management/shared-memory) — POSIX shared memory (`shm_open`) lives there for memory-management reasons.
- [File security descriptors](../access-control/file-security-descriptors) — the SD model POSIX IPC inherits.

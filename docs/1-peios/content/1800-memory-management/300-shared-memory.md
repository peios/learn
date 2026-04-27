---
title: Shared Memory
type: concept
description: Shared-memory primitives on Peios — POSIX shm, memfd, file sealing, and how the security model applies to memory shared between processes.
related:
  - peios/memory-management/memory-mapping
  - peios/IPC/ipc-object-security-descriptors
  - peios/process-security/process-security-descriptors
---

The shared-memory primitives let two or more processes see the same physical pages from their own address spaces. After setup, communication is just memory loads and stores — no syscalls per access — which is why shared memory is the highest-throughput IPC mechanism available.

This page covers the modern primitives Peios applications should reach for: POSIX shared memory, `memfd`, `memfd_secret`, and file sealing. The legacy System V SHM mechanism (`shmget`, `shmat`, `shmctl`) is honoured for compatibility but its security descriptor model is documented in the **IPC** category alongside SysV semaphores and message queues; this page focuses on the memory-side characteristics.

## POSIX shared memory

POSIX shared memory is the modern path. The interface is two calls:

| Call | Purpose |
|---|---|
| `shm_open(name, oflag, mode)` | Open or create a named shared-memory object. Returns a file descriptor. |
| `shm_unlink(name)` | Remove the name from the namespace. Existing mappings remain until unmapped. |

Under the hood, POSIX shm is **a file in `/dev/shm`** — a tmpfs-backed RAM-resident filesystem mounted at boot. `shm_open("/myshm", ...)` is roughly equivalent to `open("/dev/shm/myshm", ...)` with appropriate flags. Two processes that open the same name get fds to the same underlying file, then call `mmap(MAP_SHARED, ...)` on those fds to map the contents.

This is the cleanest design point in the shared-memory zoo because it inherits **filesystem security descriptors** automatically. The shm object has a real inode with a real SD; access control is the same AccessCheck against `READ_DATA` and `WRITE_DATA` that any other file goes through. There is no separate "shm permission" model to learn.

Practical implications:

- **Discovery.** Anyone with execute access to `/dev/shm` can list the names of existing shm objects (`ls /dev/shm`). If you don't want your shm name visible, use a random name and unlink it after both ends have opened.
- **Defaults.** A newly created shm object uses the standard file SD inheritance: parent-directory SD with the appropriate per-creator default DACL applied. Most tooling explicitly sets a restrictive mode at create time.
- **Lifetime.** The object persists until `shm_unlink` is called, even if no process has it open. The `unlink-after-mmap` pattern (open, mmap, unlink, then communicate) is idiomatic — the name vanishes but the mapping remains valid.
- **Resizing.** `ftruncate(fd, size)` sets the size; the mapping must be `mmap`'d at least that large.

There is no Peios-specific behaviour here beyond what the file SD model provides. POSIX shm is **substrate-as-is** with the access-control discussion delegated to the filesystem chapter.

## memfd_create

`memfd_create(name, flags)` creates an anonymous file in memory and returns a file descriptor. Unlike POSIX shm, the file has no name in any filesystem — it exists only as long as the fd does, plus any `mmap` regions it backs.

This is the modern primitive for "I want a chunk of shared memory I can pass to another process." The setup pattern:

1. Process A calls `memfd_create("scratch", 0)` and gets back fd `M`.
2. Process A calls `ftruncate(M, size)` and `mmap(MAP_SHARED, ..., M, 0)`.
3. Process A passes the fd to Process B over a Unix domain socket using `SCM_RIGHTS`.
4. Process B receives the fd, calls `mmap(MAP_SHARED, ..., M, 0)` with its received fd.
5. Both processes now share the same backing memory.

The security model here is **fd-bearer authority**. There is no name to look up, no permission check at `open` time — possessing the fd is the access. Process B can map the memory because Process A chose to send it the fd.

The kernel still tracks the memfd as an object with an SD for **introspection** purposes — listing entries in `/proc/<pid>/fd/` reveals memfds and is gated by the standard process SD `PROCESS_QUERY_INFORMATION` mask — but the SD does not gate the holder's use of the fd itself.

`memfd_create` flags:

| Flag | Effect |
|---|---|
| `MFD_CLOEXEC` | Set `O_CLOEXEC` on the fd, so it doesn't leak across `exec()`. Almost always wanted. |
| `MFD_ALLOW_SEALING` | Permit `fcntl(F_ADD_SEALS, ...)` on the fd. Required for any sealing to be possible. |
| `MFD_HUGETLB` | Back the memfd with hugepages. See [Huge Pages](huge-pages). |
| `MFD_NOEXEC_SEAL` | Apply `F_SEAL_EXEC` immediately at creation, preventing the memfd from ever being mapped executable. The default for newly-created memfds; must be explicitly opted out via `MFD_EXEC` for the rare cases needing executable shared memory (JIT crossing process boundaries). |

The default of `MFD_NOEXEC_SEAL` is a hardening choice: most legitimate memfd use cases never need executable mappings, and the historical pattern of "memfd containing payload, mapped executable in target process" was a popular kernel-exploit primitive. Applications that genuinely need it must say so explicitly.

## File sealing

**Sealing** is a mechanism that prevents future modifications to a file's content or layout. Once a seal is applied, the kernel refuses operations that would violate it, even if the caller has the appropriate file permissions. Seals are properties of the **file** (the inode), not of any particular fd.

Sealing only works on memfds (where `MFD_ALLOW_SEALING` was set) and on a few filesystems that explicitly support it. The seal types:

| Seal | Prevents |
|---|---|
| `F_SEAL_SEAL` | Adding any further seals. The "lock the seal set" seal. |
| `F_SEAL_SHRINK` | Truncating the file to a smaller size. |
| `F_SEAL_GROW` | Extending the file to a larger size. |
| `F_SEAL_WRITE` | Writing through any fd (`write`, `pwrite`, `splice`, etc.) and creating new writable mappings. |
| `F_SEAL_FUTURE_WRITE` | Like `F_SEAL_WRITE` but allows existing writable mappings to remain. Useful when one process holds a writer and many processes hold read-only mappings. |
| `F_SEAL_EXEC` | Mapping with `PROT_EXEC`. The default for memfds created with `MFD_NOEXEC_SEAL`. |

Seals are added with `fcntl(fd, F_ADD_SEALS, seals)`; the current set is queried with `fcntl(fd, F_GET_SEALS)`. Once applied, seals cannot be removed — the only way to drop a seal is to delete the file and start over.

The **seal-then-share** pattern is the canonical use:

1. Process A creates a memfd with `MFD_ALLOW_SEALING`.
2. Process A writes content into it.
3. Process A applies `F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE`.
4. Process A passes the fd to Process B.
5. Process B can map and read the content with confidence that it cannot change underneath them.

This is the basis of trusted-data sharing across processes that don't otherwise trust each other — Process B does not have to defensively copy the contents to guard against TOCTOU races.

## memfd_secret

`memfd_secret(flags)` creates a special memfd that is **hidden from the kernel direct map**. The pages backing the memfd are removed from the kernel's linear mapping of physical RAM, so even kernel-level code with bugs that would normally let it read arbitrary kernel memory cannot trivially read the contents.

This is a **defence-in-depth** primitive against kernel compromise. If an attacker exploits a kernel bug that gives them read access to the kernel direct map (a not-uncommon kernel-LPE primitive), they cannot read `memfd_secret` contents through that path; the kernel would have to perform an explicit mapping operation against the secret memfd, which most exploit primitives don't do.

Use cases:

- Cryptographic keys and other long-lived secrets.
- Authentication credentials held by login services.
- Pre-decrypted content waiting to be served.

Caveats:

- **Performance.** Pages backing `memfd_secret` cannot be migrated, swapped, or hugepage-backed. Don't use it for bulk data; use it for the small, sensitive subset.
- **Cross-process sharing.** `memfd_secret` regions can be shared across processes via `SCM_RIGHTS` like a normal memfd, but they cannot be made writable with `MAP_SHARED` — the kernel restricts secret memfds to read-only or process-private use. (This restriction exists because the direct-map removal is fragile across multiple writers.)
- **Not a substitute for `mlock`.** Secret memfds aren't automatically locked in RAM; you still want `MAP_LOCKED` or a follow-up `mlock` to keep them out of swap. See [Memory Locking](memory-locking).

`memfd_secret` is unprivileged — any process can create them. The protection benefits the creator, not the system, so there's no need to gate creation.

## mmap of regular files

A regular file mapped with `MAP_SHARED` is shared between every process that maps it: writes through one mapping become visible through other mappings, and are eventually written back to the file on disk. This is how dynamic linkers share library text segments across processes — the library's `.text` is `mmap`ed read-only-shared, so all processes reference the same physical pages.

The access-control gates are the file's SD. To map for `PROT_READ`, the caller needs `READ_DATA`; for `PROT_WRITE` with `MAP_SHARED`, `WRITE_DATA`; for `PROT_EXEC`, `EXECUTE`. There is no separate "permission to mmap" gate.

`MAP_PRIVATE` of a file gives the caller a **copy-on-write** view: reads see the file's content, writes go to a private anonymous copy and are not written back. This is how executables and data segments of binaries are loaded.

## See also

- [Memory mapping](memory-mapping) — the `mmap` syscall family and protection bits.
- [IPC object security descriptors](../ipc/ipc-object-security-descriptors) — the SD model for SysV SHM and other IPC objects.
- [Memory locking](memory-locking) — pinning shared regions in RAM with `mlock` or `MAP_LOCKED`.
- [Huge pages](huge-pages) — `MFD_HUGETLB` and shared hugepage memory.

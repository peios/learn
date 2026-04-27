---
title: Page Cache
type: concept
description: How Peios caches file content in memory — the page cache, readahead, fadvise/madvise hints, drop_caches, and the bypass paths.
related:
  - peios/memory-management/memory-mapping
  - peios/memory-management/swap
  - peios/memory-management/overcommit-and-oom
---

The kernel keeps recently-read file content in memory, in a structure called the **page cache**. When a process reads a file, the kernel first checks whether the requested pages are already cached; if so, the read is satisfied from RAM with no disk activity. When a process writes, the data goes into the page cache and is asynchronously flushed to disk later. The cache is **unified** across `read`/`write` syscalls and `mmap`'d file mappings — both see the same physical pages for the same file content.

The page cache is the reason software performs so much better than its disk speed alone would suggest. A workload that re-reads files repeatedly does almost no disk I/O after the first read, because the pages stay cached. The cache also amortises writes: many small writes coalesce into fewer, larger disk operations.

This page covers how to influence cache behaviour, the dirty-page writeback model, the `drop_caches` admin tool, and the bypass paths for workloads that don't want caching.

## The unified cache

All file-backed memory in the system shares the same pool of physical pages. A page representing offset 4096–8192 of `/etc/hosts` is the same physical page whether some process is reading from it via `read()`, mapping it via `mmap`, or whether the kernel itself is using it for some lookup. The page is uniquely identified by the underlying inode and offset; multiple users share access without duplication.

This unification is why `mmap`-based I/O and `read()`-based I/O have nearly identical hit rates on cached data. The choice between them is about API ergonomics and access patterns, not cache utilisation.

The historical "buffer cache" — a separate cache for block-device metadata (filesystem superblocks, inode blocks, etc.) — was integrated into the page cache long ago. Some old documentation still references it; on modern kernels everything is the page cache.

## Readahead

When a process reads a file sequentially, the kernel notices the pattern and **prefetches** subsequent pages from disk before the process asks for them. By the time the process gets to page N+1, the kernel has already pulled it into the cache.

Readahead is automatic and tuned per-device. The defaults work well for most workloads. The kernel detects sequential vs random patterns and adjusts: pure random access disables readahead entirely, pure sequential maximises it.

A process can override the kernel's pattern detection:

| Hint | Effect |
|---|---|
| `posix_fadvise(fd, off, len, POSIX_FADV_SEQUENTIAL)` | Aggressive readahead. |
| `posix_fadvise(fd, off, len, POSIX_FADV_RANDOM)` | Disable readahead for this region. |
| `madvise(addr, len, MADV_SEQUENTIAL)` | Same as `POSIX_FADV_SEQUENTIAL` but for `mmap`'d regions. |
| `madvise(addr, len, MADV_RANDOM)` | Same as `POSIX_FADV_RANDOM`. |

Per-device readahead can also be tuned at the block layer (`/sys/block/<dev>/queue/read_ahead_kb`), registry-driven via ksyncd. Workloads with unusually large or small request sizes (database storage engines, video streaming) sometimes set this explicitly.

## Explicit prefetch and eviction

Beyond pattern hints, two calls let a process directly drive cache state for its own files:

| Call | Effect |
|---|---|
| `readahead(fd, offset, count)` | Begin populating the cache with the named range. Returns immediately; the read happens asynchronously. |
| `posix_fadvise(fd, off, len, POSIX_FADV_WILLNEED)` | Same effect — start populating. |
| `posix_fadvise(fd, off, len, POSIX_FADV_DONTNEED)` | Evict the named pages from the cache. |

The eviction call is useful when a process knows it's done with a chunk of data and wants the cache space freed for other uses. The classic use case is a streaming workload that touches a file once and never again — without `POSIX_FADV_DONTNEED`, the file's pages would push other pages out of cache; with it, the streamer is a good citizen.

`mincore(addr, len, vec)` queries which pages of an `mmap`'d region are currently resident in the cache. Useful for instrumentation; rarely used for control flow.

## Dirty page writeback

When a process writes to a file (via `write()`, `pwrite()`, or stores into an `MAP_SHARED` mapping), the data goes into the page cache and the page is marked **dirty**. The kernel doesn't write dirty pages to disk immediately — it batches them, waits for opportune moments, and writes them back asynchronously. This is **writeback**.

Writeback is driven by:

- **Periodic flushing.** Every 5 seconds (default), the kernel scans for dirty pages older than 30 seconds (default) and writes them back.
- **Pressure-based flushing.** When dirty pages exceed a threshold, the kernel starts writing them back more aggressively, eventually blocking new writes if dirty data piles up faster than it can be flushed.
- **Explicit sync.** `fsync(fd)`, `fdatasync(fd)`, `sync()`, and `sync_file_range()` force writeback synchronously.

The thresholds are admin-tunable, registry-driven via ksyncd:

| Tunable | Purpose |
|---|---|
| `dirty_ratio` | Percentage of total memory at which writes start blocking. (Default 20.) |
| `dirty_background_ratio` | Percentage at which background writeback begins. (Default 10.) |
| `dirty_expire_centisecs` | How old dirty pages must be before periodic flush considers them. |
| `dirty_writeback_centisecs` | Periodic flush interval. |

Workloads with very large memory and slow disks sometimes lower `dirty_ratio` to prevent the system from accumulating gigabytes of dirty data that take minutes to flush. Workloads on fast NVMe with bursty writes sometimes raise it.

## Synchronous control with sync_file_range

`sync_file_range(fd, offset, nbytes, flags)` is the fine-grained alternative to `fsync`. It lets a process force writeback of a specific byte range, with control over whether to wait for the writes to complete. This is used by databases and other software that wants to be very precise about durability, often to drive a write-ahead log:

```c
sync_file_range(fd, log_start, log_size,
                SYNC_FILE_RANGE_WRITE | SYNC_FILE_RANGE_WAIT_AFTER);
```

Note that `sync_file_range` does **not** guarantee filesystem metadata is durable. For full durability of the metadata changes (file size, timestamps), `fsync` is still required.

## drop_caches

The `drop_caches` interface (`/proc/sys/vm/drop_caches`) is an admin tool that forcibly evicts cache contents. Writing values:

| Value | Effect |
|---|---|
| `1` | Drop page cache (file-backed pages, both clean dentries and inode caches that aren't otherwise pinned). |
| `2` | Drop slab cache (dentries and inodes). |
| `3` | Drop both. |

Writing requires admin authority — the file's SD on Peios grants `KEY_SET_VALUE` only to TCB-tier identities. The interface exists for diagnostics ("how does my benchmark perform with a cold cache?") and for occasional cache-bug workarounds; routine use in production is anti-pattern. Dropped caches will be repopulated naturally by subsequent I/O, but the immediate effect is to make the next reads slow as they go to disk.

`drop_caches` does not write dirty pages back. To get a known-quiescent cache state, write to `/proc/sys/vm/drop_caches` after running `sync(1)`.

## Direct I/O — `O_DIRECT`

A process opening a file with `O_DIRECT` opts out of the page cache entirely. Reads go straight from disk to user buffers; writes go straight from user buffers to disk. There is no caching, no readahead, no writeback delay.

`O_DIRECT` exists for workloads that have their own caching layer (databases) and don't want the kernel double-buffering. Postgres, MySQL, Oracle, and similar all support `O_DIRECT` modes.

The constraints:

- **Alignment.** Buffer addresses, file offsets, and request sizes must be aligned to the filesystem's logical block size (typically 512 bytes or 4 KB).
- **No partial reads.** A read at an unaligned offset or with an unaligned size is rejected with `EINVAL`.
- **No mmap consistency.** A file open with `O_DIRECT` and mapped via `mmap` does not coherently share data — writes via direct I/O may not be visible through the mapping until next sync. Most software avoids mixing the two.

`O_DIRECT` is not a privileged operation; any process can use it. The per-filesystem support varies — most major filesystems support it, but some don't (tmpfs and certain network filesystems, for instance), and mixing it with filesystems that don't support it returns `EINVAL`.

## DAX — direct access for persistent memory

**DAX** (Direct Access) is a path that bypasses the page cache for files on persistent-memory devices (Intel Optane DCPMM, NVDIMMs). Because the underlying storage is byte-addressable and durable, there's no benefit to caching its contents in DRAM — the persistent memory itself is the cache. With DAX enabled, `mmap`'d files on persistent-memory filesystems map directly to the persistent memory's physical addresses; loads and stores hit the persistent device directly.

This requires:

- A filesystem that supports DAX (ext4 and XFS do, on suitable devices).
- The filesystem mounted with the `dax` option (or a kernel default that selects DAX automatically for persistent-memory devices).
- `mmap` with `MAP_SYNC` for guarantees about durability semantics.

DAX is a substrate feature; Peios honours it where the underlying filesystem and hardware support it. There is no Peios-specific design here.

## Cache poisoning and isolation

A process with read access to a file can implicitly populate the page cache for that file. A subsequent reader — even one without read access — can then time their accesses to detect whether content is cached, leaking information about access patterns. This is a known timing side-channel.

Mitigations:

- **`POSIX_FADV_DONTNEED`** after handling sensitive content, to evict pages that other processes might probe.
- **Per-cgroup memory pressure**, which evicts cached pages when a cgroup approaches its limit (cgroup-aware containment).
- **`O_DIRECT`** for content that should never enter the cache.

The page cache is fundamentally shared infrastructure; absolute isolation requires opting out (with `O_DIRECT`) or accepting that some metadata about access patterns is observable to other readers of the same file.

## See also

- [Memory mapping](memory-mapping) — `MAP_SHARED` and `MAP_PRIVATE` of files; cache interaction.
- [Swap](swap) — how the page cache competes with swap for reclaim.
- [Overcommit and OOM](overcommit-and-oom) — page cache as the easiest source of reclaimable memory under pressure.

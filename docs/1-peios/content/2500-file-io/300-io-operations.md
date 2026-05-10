---
title: I/O Operations
type: concept
description: The read/write family, vectored I/O, zero-copy primitives, space management, sync, and the AIO posture (POSIX AIO, native AIO, io_uring).
related:
  - peios/file-io/overview-and-design
  - peios/file-io/opens-and-resolution
  - peios/IPC/io-uring
---

Once an fd is open, the granted mask cached on it determines what operations are permitted. This page covers the operations themselves — how data flows through the FD subsystem, the modern flag-bearing variants, and the asynchronous I/O posture.

## Read and write

| Syscall | Purpose |
|---|---|
| `read(fd, buf, n)` / `write(fd, buf, n)` | Sequential I/O. Advances the fd's offset. |
| `pread(fd, buf, n, off)` / `pwrite(fd, buf, n, off)` | Positional I/O at offset `off`. Does not change the fd's offset. Race-free with concurrent readers. |
| `readv(fd, iov, n)` / `writev(fd, iov, n)` | Vectored (scatter/gather) I/O across multiple buffers in a single syscall. |
| `preadv(fd, iov, n, off)` / `pwritev(fd, iov, n, off)` | Positional vectored I/O. |
| `preadv2(fd, iov, n, off, flags)` / `pwritev2(fd, iov, n, off, flags)` | Positional vectored I/O with per-call flags. |

`preadv2` / `pwritev2` accept a flags argument that controls per-call behaviour:

| Flag | Effect |
|---|---|
| `RWF_DSYNC` | Force write to be data-synchronous (like `O_DSYNC` for this call). |
| `RWF_SYNC` | Force write to be fully synchronous (like `O_SYNC`). |
| `RWF_HIPRI` | High-priority I/O (signals the I/O scheduler). |
| `RWF_NOWAIT` | Return `EAGAIN` rather than blocking. Useful for opportunistic I/O in event loops. |
| `RWF_APPEND` | Append-mode for this call only (independent of `O_APPEND`). |
| `RWF_UNCACHED` | Buffered I/O that drops pages from the page cache after the call completes (kernel 6.14+). |
| `RWF_NOSIGNAL` | Suppress `SIGPIPE` on a broken pipe (kernel 6.18+). Avoids the SIGPIPE/EPIPE dance. |

`RWF_UNCACHED` is documented in [Page cache](../memory-management/page-cache). It strikes a middle ground between `O_DIRECT` (no cache, alignment requirements) and standard buffered I/O (cache pollution).

## Seeking

| Syscall | Purpose |
|---|---|
| `lseek(fd, off, whence)` | Reposition the fd's offset. `whence` is `SEEK_SET`, `SEEK_CUR`, or `SEEK_END`. |
| `lseek(fd, off, SEEK_DATA)` / `SEEK_HOLE` | On sparse files, find the next region of data or hole at or after `off`. |

`SEEK_DATA` / `SEEK_HOLE` are how tools like `cp --sparse=always` efficiently walk sparse files without reading and re-detecting holes.

## Zero-copy data movement

Moving data between fds without bouncing through userspace:

| Syscall | Purpose |
|---|---|
| `sendfile(out, in, &off, n)` | Copy `n` bytes from `in` to `out` in the kernel. Originally for serving files over sockets. |
| `copy_file_range(in, &in_off, out, &out_off, n, flags)` | Filesystem-aware copy. May use server-side copy (NFSv4.2), reflinks (btrfs, XFS), or fall back to a kernel-side data copy. |
| `splice(in, &in_off, out, &out_off, n, flags)` | Move data between an fd and a pipe (or two pipes) without copying. |
| `tee(in, out, n, flags)` | Duplicate data from one pipe to another without consuming it. |
| `vmsplice(fd, iov, n, flags)` | Splice user pages into a pipe. |

`copy_file_range` is the modern preferred primitive for file-to-file copy — it can elide the data movement entirely on filesystems that support reflinks, and it can drive server-side copy on networked filesystems.

`splice` and `vmsplice` are useful for high-throughput pipe-based pipelines where the data does not need to be inspected by userspace.

## Space management

| Syscall | Purpose |
|---|---|
| `fallocate(fd, mode, off, len)` | Manipulate file space — preallocate, punch holes, collapse/insert ranges, zero a range. |
| `ftruncate(fd, len)` | Resize a file to `len` bytes. Extending creates a hole; shrinking discards data beyond `len`. |

`fallocate` modes:

| Mode | Effect |
|---|---|
| `0` | Preallocate space, ensuring future writes won't fail with `ENOSPC`. |
| `FALLOC_FL_KEEP_SIZE` | Allocate space without changing file size. |
| `FALLOC_FL_PUNCH_HOLE` | Release blocks in the range; reads return zeros. Combine with `FALLOC_FL_KEEP_SIZE`. |
| `FALLOC_FL_COLLAPSE_RANGE` | Remove a range of blocks; subsequent data shifts down. |
| `FALLOC_FL_INSERT_RANGE` | Insert a hole in the middle of the file; subsequent data shifts up. |
| `FALLOC_FL_ZERO_RANGE` | Zero a range, possibly via metadata operations rather than data writes. |
| `FALLOC_FL_UNSHARE_RANGE` | Force CoW shared blocks to be unshared in the range. |
| `FALLOC_FL_WRITE_ZEROES` | Use SSD `WRITE_ZEROES` command where available; faster than zero-writing in software (kernel 6.17+). |

Fallocate operations require `FILE_WRITE_DATA` (or `FILE_APPEND_DATA` for append-only fds) on the granted mask. Punch-hole and zero-range additionally require write access (they modify file content).

## Sync and writeback

| Syscall | Purpose |
|---|---|
| `sync()` | Initiate writeback for all dirty data on all filesystems. Returns immediately. |
| `syncfs(fd)` | Initiate writeback for the filesystem containing `fd`. |
| `fsync(fd)` | Flush data and metadata for `fd` to disk. Blocks until complete. |
| `fdatasync(fd)` | Like `fsync` but skips metadata updates not needed for data integrity (e.g., access time). |
| `sync_file_range(fd, off, n, flags)` | Fine-grained writeback control over a range. Less durable than `fsync` — does not flush filesystem journal metadata. |

`fsync` and `fdatasync` are the durability primitives. Code that needs "this data is on disk" must call one of them; pure `write()` returns when the kernel has accepted the data, not when it has hit the storage medium.

## ioctl

`ioctl(fd, request, ...)` is the catch-all device control mechanism. Each device type defines its own request codes. Commonly:

- Block devices — `BLKGETSIZE`, `BLKDISCARD`, `BLKZEROOUT`, etc.
- Filesystems — `FS_IOC_GETFLAGS`, `FS_IOC_SETFLAGS`, `FICLONE`, `FIDEDUPERANGE`, etc.
- Sockets — `SIOCGIFCONF`, `SIOCATMARK`, etc.
- Terminals — `TIOCGWINSZ`, `TCGETS`, etc.

ioctl operations are gated by the granted mask on the fd. Filesystem-mutating ioctls (e.g., `FS_IOC_SETFLAGS`) require `FILE_WRITE_ATTRIBUTES`. Device-control ioctls follow the device's own SD on the device node.

## Asynchronous I/O posture

Peios honours **three asynchronous I/O interfaces**, each with its own posture:

| Interface | Status | Recommended for |
|---|---|---|
| **POSIX AIO** (`aio_read`, `aio_write` via libc) | Shipped, libc-level (not kernel-native) | Legacy applications and portable code |
| **Native Linux AIO** (`io_setup`, `io_submit`, `io_getevents`, `io_destroy`) | Shipped intact, considered legacy | Existing applications that target it; not recommended for new code |
| **io_uring** | Shipped intact, **the preferred kernel-async interface** | New applications, high-throughput workloads |

POSIX AIO is implemented in userspace by libc using a thread pool — it does not require a special kernel interface. It works for any fd type but its performance is dominated by the thread pool overhead.

Native AIO is the kernel's original async-I/O interface. It only supports `O_DIRECT` files reliably (buffered I/O may block synchronously despite the async API). The Linux community considers it deprecated in favour of io_uring. Peios continues to ship it for compatibility with applications already targeting it.

io_uring is the modern interface — see [io_uring](../IPC/io-uring). It is the preferred surface for new asynchronous I/O on Peios.

## Authority and the granted mask

All operations on this page are gated by the granted mask cached on the fd at open time. The mask is set once and never modified. If the SD on the file changes after open, an open fd retains its grant — the handle model is "authority is on the handle, not on the holder." See [Check-at-open model](../access-control/check-at-open-model).

## See also

- [Opens and path resolution](opens-and-resolution) — the open-time gate that determines what an fd can do.
- [io_uring](../IPC/io-uring) — the modern kernel-async I/O interface.
- [Page cache](../memory-management/page-cache) — `RWF_UNCACHED` and the buffered-I/O cache model.

---
title: Pipes and FIFOs
type: concept
description: Anonymous and named pipes on Peios — pipe/pipe2/FIFO syscalls, packet mode, the splice family, and how filesystem SDs gate FIFOs.
related:
  - peios/IPC/unix-domain-sockets
  - peios/IPC/peer-credentials
  - peios/access-control/file-security-descriptors
---

A **pipe** is a unidirectional in-kernel byte buffer with a read end and a write end. Bytes written into the write end appear in order at the read end; closing one end produces predictable signal/error semantics on the other. Pipes are the original Unix IPC primitive and remain the workhorse for parent-child process composition.

This page covers anonymous pipes, named pipes (FIFOs), the splice family of zero-copy operations, and the access-control story for FIFOs.

## Anonymous pipes

`pipe(fds)` and `pipe2(fds, flags)` create a pipe and return two file descriptors: `fds[0]` is the read end, `fds[1]` is the write end. Anonymous pipes have no name in any namespace; they exist only as long as some process holds an fd to them, and their primary use is parent-child composition (set up the pipe, fork, child closes one end, parent closes the other, redirect stdin/stdout/stderr, exec).

`pipe2()` accepts flag bits at creation time:

| Flag | Effect |
|---|---|
| `O_CLOEXEC` | Close the fds on exec, so they don't leak across `execve()`. Almost always wanted. |
| `O_NONBLOCK` | The fds default to non-blocking. Reads return `EAGAIN` if no data, writes return `EAGAIN` if buffer is full. |
| `O_DIRECT` | **Packet mode.** Each `write()` produces a discrete packet readable as a single unit; `read()` returns at most one packet. Useful for message-oriented protocols. |

Without `O_DIRECT` the pipe is a byte stream — writes can be coalesced and split arbitrarily across reads.

A pipe has no security descriptor; access is by possession of the fd. The `pipe()` call is unprivileged. Closing both ends destroys the pipe; closing only the read end while the write end is open causes subsequent writes to receive `SIGPIPE` (or `EPIPE` if `SIGPIPE` is blocked).

## Named pipes (FIFOs)

A **FIFO** is a pipe with a filesystem entry. Created with `mkfifo(path, mode)` or the equivalent `mknod(path, S_IFIFO | mode, 0)`, a FIFO appears as a special file (`p` in `ls -l`) at the named path. Processes open it via the standard `open()` syscall — opening for read and opening for write produce the corresponding pipe ends.

A FIFO blocks at `open()` until both a reader and a writer are present. (`O_NONBLOCK` changes this: opening for read with `O_NONBLOCK` returns immediately whether or not a writer is present; opening for write with `O_NONBLOCK` returns `ENXIO` if no reader is present.) This rendezvous behaviour is the entire point — two unrelated processes can synchronise on the FIFO's path.

**Access control.** FIFOs use the standard filesystem security descriptor model. The FIFO's inode has an SD; opening for read requires `READ_DATA`, opening for write requires `WRITE_DATA`. There is no FIFO-specific access mask; this is a regular file SD, just on an unusual file type.

`mkfifo()` itself requires write access to the parent directory (`ADD_FILE`), same as creating any other file. The FIFO inherits its initial SD from the parent directory's inheritance rules.

Once both ends are open, the FIFO behaves identically to an anonymous pipe — same buffer semantics, same `O_DIRECT` packet mode if requested, same `SIGPIPE` on writer-after-reader-close.

## The splice family

Three syscalls move data between pipes and other file descriptors without a userspace round-trip:

| Syscall | Purpose |
|---|---|
| `splice(in, out, len, flags)` | Move bytes between a pipe and another file descriptor. At least one of `in` or `out` must be a pipe. |
| `tee(in, out, len, flags)` | Duplicate bytes between two pipes without consuming from the source. |
| `vmsplice(fd, iov, count, flags)` | Splice user pages directly into a pipe. |

The performance benefit is real. A naive "read from socket, write to file" loop copies bytes through a userspace buffer; `splice` moves them entirely in kernel space, avoiding the copies. For large transfers (file servers, proxies), the throughput difference is substantial.

The semantic gotcha: `splice` and `vmsplice` may, under the hood, take a reference to userspace pages and reuse them in the pipe buffer. A subsequent write to those pages from userspace can change what the reader eventually sees. This is documented but routinely surprises people. `vmsplice` with `SPLICE_F_GIFT` makes the gift explicit — the caller agrees not to modify the pages until the kernel has finished with them.

`splice` honours the access permissions of the underlying fds: splicing from a file fd requires the fd was opened for read (`READ_DATA`); splicing to a file fd requires write (`WRITE_DATA`). There is no separate splice-permission gate.

## Buffer size

Each pipe has a kernel-side buffer. The default size is 64 KB; it can be queried and changed:

| `fcntl` op | Purpose |
|---|---|
| `F_GETPIPE_SZ` | Query the current buffer size. |
| `F_SETPIPE_SZ` | Set the buffer size. Must be at least one page (4 KB on x86-64); upper bound capped by `pipe-max-size`. |

The upper bound (`/proc/sys/fs/pipe-max-size`) is a registry-driven sysctl applied via ksyncd. Default is 1 MB. Raising the cap is occasionally needed for high-throughput pipelining; it's an admin sysctl gated by the registry key's SD.

Per-user pipe-page limits (`pipe-user-pages-soft` and `pipe-user-pages-hard`) bound how much memory a single user's pipes can collectively consume. The Peios per-user accounting model (and its replacement of "user" with "token-projected identity" semantics) is documented in the **Resource Control** category.

## What pipes are not

Pipes do not carry credentials. There is no "peer authentication" on a pipe — the writer is just whoever holds the write fd. For authentication-bearing IPC, use Unix domain sockets ([Peer Credentials](peer-credentials)) or another primitive that can attest to peer identity.

Pipes do not provide message boundaries by default. Two writes of 100 bytes each may be coalesced into one read of 200 bytes; one write of 200 bytes may be split into two reads of 100. Use `O_DIRECT` packet mode if message preservation is required, or use a higher-level framing protocol.

Pipes are unidirectional. Bidirectional communication requires a pair of pipes. `socketpair(AF_UNIX, SOCK_STREAM)` is usually a better choice for that purpose — it's bidirectional in a single primitive and adds peer-credential attestation.

## See also

- [Unix domain sockets](unix-domain-sockets) — bidirectional IPC with peer authentication.
- [Peer credentials](peer-credentials) — peer authentication mechanisms for sockets.
- [io_uring](io-uring) — `IORING_OP_SPLICE` and `IORING_OP_TEE` for async splicing.

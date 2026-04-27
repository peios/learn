---
title: io_uring
type: concept
description: io_uring on Peios — the shared-ring async I/O interface, how it routes through standard KACS hooks, and the registry knobs for SQPOLL and URING_CMD.
related:
  - peios/IPC/epoll-and-polling
  - peios/IPC/event-fds
  - peios/access-control/access-check
  - peios/privileges/se-increase-base-priority-privilege
---

`io_uring` is Linux's high-performance asynchronous I/O interface, introduced in kernel 5.1 (2019). It eliminates much of the syscall overhead that dominates I/O-heavy workloads by replacing the per-operation syscall pattern with **two ring buffers shared between userspace and kernel**: userspace writes work requests into a submission queue, the kernel processes them and writes results into a completion queue, and (in the most aggressive mode) no syscalls are needed at all for either submission or completion harvesting.

The performance gains are real: a workload doing a million IOPS that spends 30% of CPU on syscall overhead with traditional async I/O may spend 3% with io_uring. Modern Linux software increasingly assumes io_uring's availability — recent nginx, ScyllaDB, RocksDB, Rust async runtimes, and the kernel's own NVMe-over-Fabrics target.

io_uring also has a CVE history. The complexity of the submission paths and the size of the operation set produced a steady stream of kernel bugs in its first few years. Modern (kernel 6.x) io_uring is much more mature, and the access-control story has been hardened in step. This page covers the architecture, the access-control model on Peios, and the registry knobs that let operators tune availability.

## The architecture

A process calls `io_uring_setup(entries, &params)` and gets back an fd. The kernel `mmap`s two ring buffers into the process's address space:

- **Submission Queue (SQ).** An array of submission queue entries (SQEs). Each SQE describes one operation: an opcode, a target (fd), an address, a length, and operation-specific arguments.
- **Completion Queue (CQ).** An array of completion queue entries (CQEs). Each CQE reports the result of one previously-submitted operation: a return value plus user-data the submitter attached.

Userspace fills SQEs at the SQ tail; the kernel processes them and writes CQEs at the CQ tail. Both ring tails and heads are shared variables in the mmapped region, so userspace and kernel can both read and write them without syscalls.

The process tells the kernel "go check the SQ" via `io_uring_enter()`, which is one syscall amortising across many operations. Or — see SQPOLL below — it can avoid that syscall entirely.

## The operation surface

io_uring has grown to support a long list of operations:

| Category | Operations |
|---|---|
| Block I/O | `READV`/`WRITEV`/`READ`/`WRITE`/`READ_FIXED`/`WRITE_FIXED`, `FSYNC`/`FDATASYNC`, `SYNC_FILE_RANGE`, `FALLOCATE` |
| Network | `SENDMSG`/`RECVMSG`/`SEND`/`RECV`, `ACCEPT`/`CONNECT`/`SOCKET`/`SHUTDOWN`, `SEND_ZC`/`RECV_ZC` (zero-copy) |
| Filesystem | `OPENAT`/`OPENAT2`/`CLOSE`/`STATX`, `RENAMEAT`/`UNLINKAT`/`MKDIRAT`/`SYMLINKAT`/`LINKAT` |
| Pipes | `SPLICE`/`TEE` |
| Polling | `POLL_ADD`/`POLL_REMOVE`, `EPOLL_CTL` |
| Timers | `TIMEOUT`/`TIMEOUT_REMOVE`/`LINK_TIMEOUT` |
| Process | `WAITID` |
| Cancellation | `CANCEL`/`ASYNC_CANCEL` |
| Sync primitives | `FUTEX_WAIT`/`FUTEX_WAKE`/`FUTEX_WAITV` |
| Hints | `FADVISE`/`MADVISE` |
| Buffer mgmt | `PROVIDE_BUFFERS`/`REMOVE_BUFFERS`, `FILES_UPDATE` |
| xattrs | `FGETXATTR`/`FSETXATTR`/`GETXATTR`/`SETXATTR` |
| Driver passthrough | `URING_CMD` |

The list is essentially "every common syscall plus some bonuses." io_uring is functionally a *second syscall ABI*; anything you can do via a normal syscall, you can probably do via io_uring with lower overhead.

## How access control works

The natural worry — does this huge alternative ABI need its own parallel access-check infrastructure? — is answered cleanly by the kernel's hook architecture. io_uring **routes its operations through the same kernel-internal access-decision hooks that ordinary syscalls do.** It's a "second ABI" only at the userspace-facing layer; below that, every operation lands on the standard hook points.

`IORING_OP_OPENAT` calls `security_file_open` exactly like the `openat()` syscall does. `IORING_OP_SENDMSG` calls `security_socket_sendmsg`. `IORING_OP_UNLINKAT` calls `security_path_unlink`. KACS, plugged into these standard hook points, sees io_uring operations alongside their syscall equivalents and authorises them through the same AccessCheck path. There is no separate "io_uring AccessCheck model."

The non-trivial cases got their own io_uring-specific hooks added in kernel 5.16-ish:

- **`security_uring_override_creds`** fires when the SQPOLL kernel thread is about to assume the registering process's credentials for SQE processing. KACS uses this hook to validate the credential override.
- **`security_uring_sqpoll`** fires at `io_uring_setup` time when `IORING_SETUP_SQPOLL` is requested. KACS uses this hook to enforce the SQPOLL privilege gate.
- **`security_uring_cmd`** fires when `IORING_OP_URING_CMD` is submitted. KACS uses this hook to enforce the URING_CMD policy.

Submission-time AccessCheck applies even for fixed-file optimisations: io_uring re-runs the access hooks at submission for every operation, regardless of whether the underlying fd was pre-registered. Pre-registration is purely a fast-path optimisation; it does not bypass authorisation. This was the post-CVE Linux fix and is part of the substrate Peios inherits.

## SQPOLL — kernel-thread polling

`IORING_SETUP_SQPOLL` requests that the kernel spawn a dedicated thread to *busy-poll* the submission queue. With SQPOLL, userspace doesn't need to call `io_uring_enter` at all — the kernel thread continuously checks the SQ for new SQEs and processes them.

The performance benefit is significant for very-high-throughput workloads. The cost: a kernel thread spinning on userspace memory, consuming a CPU. Multiple SQPOLL setups can pin lots of CPU on polling threads.

**Privilege gate.** SQPOLL setup requires **`SeIncreaseBasePriorityPrivilege`**. This is the same privilege that gates raising scheduling priority, on the reasoning that SQPOLL is a "spend kernel CPU on me" request — operationally the same category as priority bumps. Default holders are TCB-tier services (peinit, performance-critical daemons that legitimately need SQPOLL for their I/O patterns). Unprivileged code falls back to standard `io_uring_enter`-based submission, which works fine for moderate workloads.

After a brief idle period, the SQPOLL thread sleeps to free the CPU; subsequent submissions wake it via `io_uring_enter` with `IORING_ENTER_SQ_WAKEUP`. The privilege gate prevents unbounded CPU consumption from idle pollers.

## URING_CMD — driver passthrough

`IORING_OP_URING_CMD` submits an opaque command directly to a device driver, bypassing the standard kernel syscall surface. The driver receives a buffer of bytes; it interprets them however it wants. This is how NVMe pass-through works (raw NVMe commands sent to disks), and how some filesystem-pass-through mechanisms operate.

The risk is real. A driver bug accessed via `URING_CMD` is potentially reachable by anyone who can submit io_uring SQEs against the device, bypassing the abstraction layers and validation that normal syscalls go through. Even with proper device SDs, exposing raw driver command channels to arbitrary submission queues is a substantive attack surface.

**Policy.** A registry-driven knob controls URING_CMD availability:

| Value | Behaviour |
|---|---|
| `permit` | URING_CMD operations succeed if the device fd's SD permits. (Linux default behaviour.) |
| `disabled` | URING_CMD operations always fail with `EOPNOTSUPP`. |

The default is `permit` to match Linux behaviour and avoid breaking high-throughput-storage workloads (NVMe-pass-through being the canonical legitimate use). Fortress-mode images flip the knob to `disabled` to shut the surface entirely. The knob is gated by the registry key's SD; tightening is administratively scoped, and the knob can only tighten — there is no path to "more permissive than Linux."

## io_uring availability

A second registry knob controls io_uring availability at a higher level:

| Value | Behaviour |
|---|---|
| `default` | io_uring is fully available. |
| `restricted` | `io_uring_setup()` succeeds only if `IORING_SETUP_R_DISABLED` is also passed, requiring the process to use `IORING_REGISTER_RESTRICTIONS` to opt into a constrained operation set before submitting any SQEs. |
| `disabled` | `io_uring_setup()` always fails with `ENOSYS`. io_uring is functionally absent. |

The default is `default`. Fortress images set `disabled` for hard exclusion or `restricted` to require explicit operation-whitelisting. The build-time `CONFIG_IO_URING=n` is also available for kernels that should not include io_uring code at all.

## IORING_REGISTER_RESTRICTIONS — sandbox-friendly mode

A process can voluntarily restrict its own io_uring instance to a whitelist of allowed operations and fds. The flow:

1. Set up io_uring with `IORING_SETUP_R_DISABLED` (the instance is initially inert).
2. Register the allowed operation set, fd table, and per-op constraints via `io_uring_register(IORING_REGISTER_RESTRICTIONS, ...)`.
3. Enable the instance via `IORING_REGISTER_ENABLE_RINGS`.

After enable, the registered restrictions are immutable — the process cannot remove restrictions later. Operations outside the whitelist fail with `EACCES`.

This is the recommended pattern for sandboxed processes that want io_uring's performance without exposing its full surface. A web browser's content process, a sandboxed media decoder, a constrained worker — all benefit from registering only the operations they actually need (perhaps just `READ`/`WRITE`/`SEND`/`RECV` on a small fd set) and refusing everything else.

The combination of `restricted` mode (image-level) and per-process restrictions (process-level) gives operators and applications layered control over the io_uring surface.

## Fixed files and fixed buffers

For sustained high-throughput workloads, two registration mechanisms amortise per-operation costs:

| Mechanism | Effect |
|---|---|
| **Fixed files** (`IORING_REGISTER_FILES`) | Pre-register an fd table; SQEs reference fds by index instead of value, saving a per-operation lookup. |
| **Fixed buffers** (`IORING_REGISTER_BUFFERS`) | Pre-register userspace buffers; the kernel pins them in memory so I/O can complete without per-operation buffer setup. |

These are performance optimisations only. As noted above, AccessCheck still runs at submission time for every operation regardless of fixed-file/buffer registration. The optimisations save *lookup* work, not *authorisation* work.

## When to use io_uring

io_uring is the right choice when:

- Throughput is the bottleneck and syscall overhead dominates.
- The workload submits many operations in batches (network servers, databases, storage proxies).
- Async semantics fit naturally (request submitted, do something else, handle completion).

For lighter workloads — a few connections, low-throughput, simple control flow — `epoll` plus regular blocking syscalls is simpler and adequate. The complexity cost of io_uring (and the larger attack surface) is not free.

For sandboxed and security-sensitive contexts, prefer the `restricted` mode with explicit operation registration, or fall back to standard syscalls entirely. io_uring is a power tool; like all power tools, it should be used where the leverage is needed.

## See also

- [epoll and polling](epoll-and-polling) — the simpler readiness-check primitives for moderate workloads.
- [Event-bearing file descriptors](event-fds) — the event-source primitives io_uring can consume.
- [Access check](../access-control/access-check) — the standard AccessCheck path that io_uring operations route through.

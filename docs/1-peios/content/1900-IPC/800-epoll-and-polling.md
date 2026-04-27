---
title: epoll and Polling
type: concept
description: File-descriptor readiness on Peios — epoll, poll, select, and the patterns for high-throughput event-driven services.
related:
  - peios/IPC/event-fds
  - peios/IPC/io-uring
  - peios/IPC/unix-domain-sockets
---

A file descriptor is **ready** when an operation on it would not block. A socket is ready-for-read when bytes have arrived; a pipe is ready-for-write when its buffer has room; a signalfd is ready-for-read when a signal has been raised. Most network and IPC code is ultimately a loop that waits for readiness, handles whichever fds became ready, and waits again.

Linux exposes three readiness-checking primitives: `select`, `poll`, and `epoll`. They differ in how they're configured and how they scale. `epoll` is the modern path for any non-trivial workload; `select` and `poll` exist for compatibility and simplicity.

This page is mostly substrate documentation — the readiness mechanisms work on Peios identically to Linux, with no Peios-specific access control beyond the per-fd permissions of the fds being polled.

## select

`select(nfds, &readfds, &writefds, &exceptfds, &timeout)` is the original Unix readiness primitive. The caller passes three bitsets of fds (read, write, exceptional condition), and a timeout. The kernel checks each, blocks until at least one is ready or the timeout expires, and returns with the ready bitsets modified to indicate which fds matched.

The bitset is a fixed-size structure (`fd_set`) with capacity defined by `FD_SETSIZE`, typically 1024. fds with values ≥ 1024 cannot be polled with `select`; they must use `poll` or `epoll`.

`pselect6` is the same with two extras: a nanosecond-precision timeout, and a signal mask that's atomically applied for the duration of the wait (avoiding the race between unblocking signals and entering the wait).

`select` is straightforward but inefficient at scale: every call rebuilds the kernel-side fd watch list from scratch, costing O(nfds) per invocation. For a server with thousands of connections, this overhead dominates.

## poll

`poll(&fds[], nfds, timeout)` is the second-generation readiness primitive. The caller passes an array of `struct pollfd` entries, each naming an fd and a bitmask of events to watch for. The kernel checks each fd, blocks until ready, and writes back which events occurred.

`ppoll` adds the signal-mask atomicity feature analogous to `pselect6`.

Advantages over `select`:

- No `FD_SETSIZE` limit; `poll` handles any fd value.
- Per-fd granular event masks (rather than the three-bitset model).
- Slightly cleaner API.

Disadvantages: still O(nfds) per call. The kernel walks the entire array on every invocation. For workloads with many idle connections and few active, this is wasteful.

## epoll

`epoll` is the modern Linux readiness mechanism. It separates **interest registration** (telling the kernel which fds you care about and which events) from **wait-for-events** (asking the kernel "what's ready right now?"). The kernel maintains the watch list across calls; you only walk fds that have actually become ready.

The three primitive calls:

| Syscall | Purpose |
|---|---|
| `epoll_create1(flags)` | Create an epoll instance. Returns an fd that itself can be polled (nested epoll). |
| `epoll_ctl(epfd, op, fd, &event)` | Add (`EPOLL_CTL_ADD`), modify (`EPOLL_CTL_MOD`), or remove (`EPOLL_CTL_DEL`) a watched fd. |
| `epoll_wait(epfd, events[], maxevents, timeout)` | Block until events occur; return the list of ready fds. |

`epoll_create1` flags: `EPOLL_CLOEXEC` (close on exec).

`epoll_pwait` and `epoll_pwait2` are the signal-mask-atomic variants; `epoll_pwait2` adds nanosecond timeout precision.

### Event flags

The events watched on a per-fd basis:

| Flag | Effect |
|---|---|
| `EPOLLIN` | fd is ready for read. |
| `EPOLLOUT` | fd is ready for write. |
| `EPOLLERR` | fd has an error condition. |
| `EPOLLHUP` | fd has hung up (write end closed for pipes/sockets). |
| `EPOLLRDHUP` | fd's read end has hung up (peer closed for sockets). |
| `EPOLLPRI` | Out-of-band data on the fd. |

These are the level-triggered events; the fd remains ready as long as the underlying condition holds. Event modifiers change the trigger semantics:

| Modifier | Effect |
|---|---|
| `EPOLLET` | Edge-triggered. The fd reports ready only at the moment of the transition; the consumer must drain it completely before the next wait. |
| `EPOLLONESHOT` | After one notification, the fd is automatically deleted from the watch list. The consumer must `EPOLL_CTL_MOD` to re-arm. |
| `EPOLLEXCLUSIVE` | When multiple epoll instances are watching the same fd, only one of them is woken. Defeats the thundering-herd problem in multi-acceptor architectures. |
| `EPOLLWAKEUP` | Prevents system suspend while the event is being handled. Used by power-aware code to indicate "I'm doing something important; don't go to sleep." Requires `SeWakeFromSleepPrivilege`. |

### Edge-triggered vs level-triggered

The fundamental performance distinction. **Level-triggered** (the default) reports an fd as ready as long as the operation would not block. If the consumer reads only some of the available data, the fd remains ready and `epoll_wait` returns it again. This is the "obvious" semantics and works without surprises.

**Edge-triggered** (`EPOLLET`) reports an fd as ready *only at the moment* it transitions from not-ready to ready. The consumer must read until the operation would block (`EAGAIN`); otherwise the next `epoll_wait` will not return the fd, even though more data is buffered. Edge-triggered is more efficient for high-throughput workloads (one wake per event-batch instead of per-byte) but requires careful programming.

### Nested epoll

`epoll` instances are themselves fds and can be added to other `epoll` instances. This lets a server compose multiple watch sets — one for slow connections, one for fast ones, one for control fds — into a single waiter. The composition is bounded (the kernel imposes a depth limit to prevent infinite recursion) but supports realistic multi-tier event-loop architectures.

## Choosing the right primitive

| Use case | Recommended |
|---|---|
| Few fds, simple code | `poll` or `select` |
| Many fds, scale matters | `epoll` |
| Highest scale, async I/O | `io_uring` (see [io_uring](io-uring)) |

For new code on Peios at any scale beyond a handful of fds, `epoll` is the right choice. `io_uring` goes further when the workload is I/O-heavy and benefits from queued submission, but `epoll` is simpler and covers a broader range of event sources (signals, timers, process exits via pidfd) uniformly.

## Composability with event-bearing fds

The whole point of having `signalfd`, `timerfd`, `eventfd`, and pidfd is that they're fds — they participate in the same readiness machinery as everything else. A canonical Peios event loop:

```c
int epfd = epoll_create1(EPOLL_CLOEXEC);

epoll_ctl(epfd, EPOLL_CTL_ADD, listen_socket, &(struct epoll_event){.events = EPOLLIN});
epoll_ctl(epfd, EPOLL_CTL_ADD, signalfd, &(struct epoll_event){.events = EPOLLIN});
epoll_ctl(epfd, EPOLL_CTL_ADD, timerfd, &(struct epoll_event){.events = EPOLLIN});
epoll_ctl(epfd, EPOLL_CTL_ADD, child_pidfd, &(struct epoll_event){.events = EPOLLIN});

while (running) {
    struct epoll_event events[64];
    int n = epoll_wait(epfd, events, 64, -1);
    for (int i = 0; i < n; i++) {
        /* dispatch by which fd became ready */
    }
}
```

One loop, all event sources unified. This is the canonical pattern; modern Peios services should look approximately like this.

## Access control

`epoll` itself is not access-controlled — the epoll instance is local to the calling process, and adding fds to it requires only that the caller hold those fds. There is no privileged epoll mode.

The fds being polled have whatever access controls their underlying objects impose. Polling a socket fd requires holding the fd; that's all. Polling a fd you've received via `SCM_RIGHTS` works just as well as polling a fd you opened yourself.

## See also

- [Event-bearing file descriptors](event-fds) — the fds that produce events for `epoll` to consume.
- [io_uring](io-uring) — the higher-scale async-I/O alternative.
- [Unix domain sockets](unix-domain-sockets) — a common source of poll-able fds.

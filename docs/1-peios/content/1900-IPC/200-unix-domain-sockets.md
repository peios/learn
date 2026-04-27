---
title: Unix Domain Sockets
type: concept
description: Unix domain sockets on Peios — socket types, the three address forms, and the security implications of the abstract namespace.
related:
  - peios/IPC/peer-credentials
  - peios/IPC/fd-passing
  - peios/IPC/pipes-and-fifos
  - peios/access-control/file-security-descriptors
---

A **Unix domain socket** uses the same socket API as TCP/UDP — `socket()`, `bind()`, `connect()`, `accept()`, `send()`, `recv()` — but the data never leaves the kernel. Instead of routing through a network stack, the kernel hands bytes from one socket buffer to another in memory. Unix sockets are the standard mechanism for high-throughput IPC on a single host: faster than pipes (no per-byte syscall, batched send/recv), more flexible (bidirectional, multiple-client server pattern), and they support fd-passing — see [FD Passing](fd-passing).

This page covers the socket types, the three address forms, and the security characteristics — particularly the abstract namespace, which is a Linux-specific quirk worth understanding before using.

## Socket types

`socket(AF_UNIX, type, 0)` creates a socket of one of three types:

| Type | Semantics |
|---|---|
| `SOCK_STREAM` | Byte stream, connection-oriented. Like TCP. The most common type — D-Bus, X11, most desktop session managers. |
| `SOCK_DGRAM` | Datagram, connectionless, message-preserving (each `send` produces one `recv`). Reliable and ordered (unlike UDP, which loses these guarantees). |
| `SOCK_SEQPACKET` | Sequenced datagram, connection-oriented, message-preserving. Combines the connection model of `SOCK_STREAM` with the message boundaries of `SOCK_DGRAM`. |

`SOCK_RAW` is also accepted by the syscall on Linux for backward compatibility with some applications but produces a socket equivalent to `SOCK_DGRAM`; it has no special raw semantics in the AF_UNIX family.

The choice between stream and seqpacket is mostly a style choice — both produce reliable connections, but seqpacket preserves message boundaries while stream does not.

## socketpair

`socketpair(AF_UNIX, type, 0, fds)` creates a pre-connected pair of sockets and returns their file descriptors. The pair is anonymous (no address), so it's the same use case as anonymous pipes: parent-child composition, where you set up the pair, fork, and use it as the channel between the two processes.

The advantage over pipes: socketpair is bidirectional in a single primitive, supports peer-credential attestation, and supports fd-passing. The cost is slightly more setup overhead. For parent-child IPC, prefer `socketpair` over `pipe`.

## The three address forms

A Unix socket needs an address only if unrelated processes need to find each other. Linux supports three forms:

### Pathname

The socket is bound to a filesystem path. `bind()` creates a special file at the path (a "socket" file, `s` in `ls -l`); other processes `connect()` by passing the same path. When the socket closes, the file remains until explicitly `unlink()`'d — leftover socket files are a routine source of "address already in use" errors at restart.

Pathname sockets use the standard filesystem SD model. Connecting requires `WRITE_DATA` on the socket file (counterintuitively — the standard Linux convention treats `connect` as a write because it's writing to the listener). Binding requires `ADD_FILE` on the parent directory and `WRITE_OWNER` if the SD inheritance rules require it. There is no socket-specific permission model; it's a regular file SD.

This is the **safe choice for security-sensitive services**. The path's SD governs who can connect; the path is enumerable in the filesystem with normal tooling; cleanup at exit is a simple `unlink`. Most well-engineered services on Peios bind their sockets in `/run/...` or `/var/run/...` and use the SD to control client access.

### Unnamed

`socketpair()` produces unnamed sockets — no address, no namespace presence, just a connected pair of fds. Authentication is by fd-passing: whoever holds an fd to the pair can use it. Unnamed sockets are the right choice for ephemeral, parent-child, or fd-handoff IPC.

### Abstract namespace

The third form is **Linux-specific** and worth understanding because it has security characteristics distinct from the other two. The address is a string starting with a NUL byte: `\0name`. There is no filesystem entry; the name lives in a kernel-internal table scoped per network namespace.

Abstract sockets exist because pathname sockets have operational annoyances:

- A pathname socket leaves a file behind if the owning process crashes; the next start fails with `EADDRINUSE` until the file is `unlink`'d.
- Pathname sockets need a writable filesystem to bind on. In containers with read-only roots, finding a writable directory is friction.
- Pathname sockets pick up filesystem permission inheritance from the parent directory, which surprises people who expected fresh defaults.

Abstract namespace solves these by avoiding the filesystem entirely.

## The abstract-namespace footguns

The trade-off is **no security descriptor**. Whoever wins `bind()` first owns the name, and any process in the same network namespace can `connect()`. Issues that have produced real CVEs and audits:

**Race-to-bind.** A privileged service binds `\0com.example.broker` at startup. An attacker who runs first (perhaps after crashing the service to trigger a restart window) gets to impersonate the broker. Clients connect to the imposter, send credentials, and the attacker collects them.

**Squatting.** A service expects to bind a known name. An unprivileged process binds it first; the service's `bind()` fails. The service crashes (DoS) or falls back to a different name and clients don't find it.

**Cross-tenant leakage.** Abstract sockets are scoped to the network namespace. Containers sharing a netns (most rootful Docker setups before user namespaces) share the abstract namespace, allowing one container to talk to or impersonate another's services.

**Surprise visibility.** `ss -lx` lists abstract sockets system-wide. A process leaking an abstract name (in command-line arguments, environment variables, log lines) gives every observer the address to connect to.

D-Bus, systemd, and several Linux desktop services have had abstract-socket-related issues; the broader Linux community has been gradually migrating high-value services to pathname sockets in `/run/...` exactly because pathname sockets carry SDs and abstract ones don't.

## The Peios posture

Abstract namespace is supported as substrate-as-is for compatibility — too much existing Linux software depends on it. The Peios documentation is loud about the footguns:

- **Use pathname sockets in `/run/<service>/`** for any service performing authentication. The path's filesystem SD provides real access control.
- **Use abstract sockets** only for unauthenticated discovery patterns where any local process is a legitimate participant — and even then, prefer pathname sockets if the service is security-relevant.
- **Use socket activation** at boot, where peinit (or another supervisor) binds the canonical socket address on behalf of a service before the service starts. This eliminates the race-to-bind window.

A future Peios revision may introduce an `SeCreateAbstractSocketPrivilege` that gates `bind()` to the abstract namespace, raising it from "anyone may squat" to "only TCB-tier services may create abstract sockets." This would substantially reduce the squatting surface without breaking unprivileged `connect()`. The change would be visible in a future release; current images do not enforce this gate.

## Multi-listener and connection patterns

The standard server pattern works as on TCP:

1. `socket()` to create.
2. `bind(addr)` to give it an address.
3. `listen(backlog)` to accept connections.
4. `accept()` in a loop, returning a new fd per connected client.

`SOCK_DGRAM` doesn't use `listen`/`accept`; it's connectionless, and a single bound socket receives datagrams from any sender via `recvfrom`/`recvmsg`.

`SO_PEERCRED` and friends, documented in [Peer Credentials](peer-credentials), provide the kernel-attested peer identity for connection-oriented Unix sockets. `SCM_CREDENTIALS` provides per-message peer identity for `SOCK_DGRAM` and `SOCK_SEQPACKET`.

## See also

- [Peer credentials](peer-credentials) — the SO_PEERCRED, SO_PEERTOKEN, SCM_CREDENTIALS family for client authentication.
- [FD passing](fd-passing) — `SCM_RIGHTS` for moving fds between processes via Unix sockets.
- [Pipes and FIFOs](pipes-and-fifos) — the simpler unidirectional alternative.
- [File security descriptors](../access-control/file-security-descriptors) — how pathname-socket SDs work.

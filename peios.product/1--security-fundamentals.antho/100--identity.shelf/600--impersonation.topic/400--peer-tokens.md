---
title: Peer tokens and capture
type: concept
description: How the kernel captures a client's identity onto a socket at connect, the socket option and libpeios calls that use it, which transports carry peer tokens, and identity cascading.
related:
  - peios/impersonation/overview
  - peios/impersonation/impersonation-levels
  - peios/impersonation/the-two-gates
---

When a client connects to a server over a connected Unix socket, the kernel captures the client's identity onto the socket at connect time. The server can later impersonate that identity by calling `peios_token_impersonate_peer(fd)` on the connection — no further negotiation, no credential exchange, no token transfer in the message stream. The token is held by the kernel and tagged to the socket from the moment of connect.

This is the primary way servers acquire impersonation tokens. Almost every local IPC in Peios — registry access, service-to-service calls, user-to-daemon requests — goes through it. The model is simple enough that most services need to know only one call (`peios_token_impersonate_peer`) and one cleanup call (`kacs_revert`).

The kernel surface behind it is a socket option. Every KACS socket option lives under one option level, `SOL_KACS`, and the peer token is `getsockopt(fd, SOL_KACS, KACS_SO_PEER_TOKEN, &token_fd, &len)` on the accepted connection: the kernel writes a new token fd into the option value. libpeios wraps that as `peios_token_open_peer(fd)`, and `peios_token_impersonate_peer(fd)` is the same call followed by an install and a close.

This page covers the capture mechanism, the two ways of using a captured peer token, the transports that do and do not carry peer tokens, and how identity cascades when a service that is itself impersonating connects to a third service.

## Capture at connect time

```mermaid
flowchart LR
    A["Client thread, primary token T_C"] -->|"KACS_SO_IMPERSONATION_LEVEL (optional)"| B["Socket"]
    A -->|connect| C["Server socket"]
    B -.->|captured at connect| D["Peer token on server side, derived from T_C at the client-requested level"]
```

When the client calls `connect()` on a Unix stream or seqpacket socket, the kernel:

1. Reads the client's effective token (impersonation if set, primary otherwise).
2. Reads the impersonation level the client requested on the socket with `KACS_SO_IMPERSONATION_LEVEL` (default Impersonation). The option can be changed at any time; it bounds every capture made from then on.
3. Constructs a peer token derived from the client's token, at the requested level.
4. Attaches the peer token to the server-side socket.

The peer token is held by the kernel for the life of the socket. The client's identity travels into the kernel at connect, not at impersonate. By the time the server reads the peer token, the work of capturing identity is already done.

What the server reads is the connection's **conveyed-identity register**: the peer identity that goes with the data the server has consumed so far. The connect-time capture is its first value, and it stays that unless the client conveys a new identity with the data itself (next section). Whatever it holds, it is always an immutable snapshot — each read of `KACS_SO_PEER_TOKEN` returns a fresh fd, two reads may name different tokens, but no token ever changes under you.

## Identity that travels with the data

A single identity per connection is the right model for a client that connects, acts as itself, and disconnects. It is the wrong model for two things real systems do constantly:

- **Connection pooling.** A service keeps a few long-lived connections to a downstream service and reuses them for many requests, on behalf of many different users. The identity at connect time is the pool's; the identity that matters is whoever is writing *this* request.
- **Proxies and routers.** One process accepts from many clients and forwards their messages over its own connections. Its outbound connection carries one connect-time identity, but it is speaking for many.

Both are solved by letting identity travel in-band, attached to the bytes it describes, as a `KACS_SCM_TOKEN` ancillary message under the `SOL_KACS` level. It arrives ordered with the data — the kernel never coalesces bytes conveyed under different identities into one read — and as the server's reads pass each one, the register moves to it. There is nothing to listen for: the server reads a request, then asks `KACS_SO_PEER_TOKEN` who sent it.

There are two ways to send it, and the receiver cannot tell them apart, because the kernel guarantees the same thing for both: *the sender could be this identity when it sent these bytes*.

- **Automatically**, by setting `KACS_SO_PASS_TOKEN` on the sending socket (`peios_socket_set_pass_token`). From then on every send carries the sender's effective identity, derived at the socket's impersonation level. This is the fix for pooling: a service that impersonates user A and writes through an off-the-shelf client library conveys A, because the capture happens at the `sendmsg` the library was already calling. Nothing in the library changes.
- **Explicitly**, by attaching a token fd in a `KACS_SCM_TOKEN` cmsg on `sendmsg`. This is the fix for proxies: the router holds each client's token fd (read from its own inbound connection) and attaches it to the messages it forwards downstream. The kernel gates the attach as if the sender were impersonating that token — the fd needs `TOKEN_IMPERSONATE`, and if the two-gate model would cap the token below its own level the send fails with `EPERM` rather than quietly downgrading. Attaching is never more than impersonating, sending, and reverting; it just skips the install.

On the receiving side, a `KACS_SCM_TOKEN` cmsg (carrying a fresh `TOKEN_QUERY | TOKEN_IMPERSONATE | TOKEN_DUPLICATE` fd) is delivered with a read when the call supplied control-buffer space and the read's identity differs from what the register held. A server that never touches ancillary data loses nothing — the register is kept by the kernel regardless — which makes the simple loop the right default:

```c
n = recvmsg(conn, &msg, 0);              /* just the data */
tok = peios_token_open_peer(conn);       /* who sent what I just read */
```

Parsing the cmsg is the path for pipelined or concurrent consumers that need each token bound to a specific message. `SOCK_SEQPACKET` keeps that association exact by construction (one send, one message, one identity), which is why it is the recommended socket type for Peios-native protocols; on `SOCK_STREAM` a read simply stops at each identity boundary.

Datagram sockets have no register (many senders share one socket), so on `SOCK_DGRAM` per-message identity is the only kind: each datagram carrying a token delivers it.

## Two ways to use a peer token

libpeios exposes two operations on a peer token:

- **`peios_token_impersonate_peer(fd)`** — the combined operation. Reads the peer's identity from the socket and installs it on the calling thread, at the level the two-gate model permits, then closes the token fd. The most common path.
- **`peios_token_open_peer(fd)`** — the inspect-and-store operation: `getsockopt(SOL_KACS, KACS_SO_PEER_TOKEN)`. Returns a token fd to the peer's identity without installing it. The fd carries `TOKEN_QUERY | TOKEN_IMPERSONATE | TOKEN_DUPLICATE` access — enough to read the token, to install it later via `KACS_IOC_IMPERSONATE`, and to duplicate it (for instance to a primary token for a process launched as the client), but not enough to adjust it. Duplicating never raises the level: the copy is capped at whatever the client granted.

The two operations exist because servers have different needs:

- **Direct request handling.** A request thread that wants to impersonate, do work, and revert all in one tight synchronous block calls `peios_token_impersonate_peer` and then `kacs_revert`. There is no reason to hold the token fd around.
- **Just-in-time impersonation.** A server that wants to keep the client's identity available across a request but only install it at the moment of each access-requiring action — the [just-in-time pattern](~peios/impersonation/overview) covered on the overview page — calls `peios_token_open_peer` to capture the token fd at request start, stores it in the request context, and installs it on the current OS thread (`KACS_IOC_IMPERSONATE`) just before each action that needs the client's identity, reverting immediately after. This is the right pattern for any server using a multiplexed runtime (Go, Rust async, Java virtual threads, Node), and is the recommended default for new services.
- **Deferred work across threads.** A request handler that hands off work to a thread pool cannot reasonably keep its own thread impersonating while another thread does the work — impersonation is per-thread. The same `peios_token_open_peer` mechanism lets it capture the token fd, pass it to the worker, and have the worker install it before doing the access-requiring operation.
- **Inspection without action.** A logging or audit thread that wants to record the client's identity without doing any work as them calls `peios_token_open_peer`, queries the token via `KACS_IOC_QUERY`, and closes the fd. No impersonation is ever installed.

The "capture once, install per action" pattern is the main reason for separating the two operations. It is what makes safe impersonation possible under M:N threading and what bounds the time a thread is actually impersonated to the smallest window that does the work.

## kacs_revert and the explicit-fd variant

A thread reverts impersonation with `kacs_revert()`. It always succeeds. It drops the impersonation token reference and restores the primary as the effective identity.

There is also `KACS_IOC_IMPERSONATE` — an ioctl on a token fd, not on a socket. This is the explicit-fd variant. The caller passes the fd of a token they have obtained by some other means (DuplicateToken, the peer-token option, etc.) and the kernel installs it on the calling thread, running the two-gate model as usual.

`peios_token_impersonate_peer` is exactly `peios_token_open_peer` followed by `KACS_IOC_IMPERSONATE` and a close, fused for the common case where you do not need the token fd to outlive the impersonate-and-revert cycle. It is a library convenience: the kernel's only impersonation entry is the ioctl.

## Transports that carry peer tokens

Peer token capture works on Unix sockets that have a real **connect** step. Specifically:

| Transport | Peer token? |
|---|---|
| `SOCK_STREAM` Unix socket | **Yes.** Captured at connect; register follows conveyed identity. |
| `SOCK_SEQPACKET` Unix socket | **Yes.** Captured at connect; register follows conveyed identity. |
| `SOCK_DGRAM` Unix socket | **Per message only.** No connect step, so nothing to capture and no register (`KACS_SO_PEER_TOKEN` fails with `EOPNOTSUPP`), but `KACS_SO_PASS_TOKEN` and `KACS_SCM_TOKEN` work on every datagram. |
| `socketpair(2)` | **Per message only, with a register.** The two ends share an origin, so nothing is captured (`ENODATA` at first) — but the moment one end conveys an identity, the other's register holds it. The way a broker's private channels get identity. |
| Pipes (`pipe(2)`, named FIFOs) | **No.** Not sockets at all: `ENOTSOCK`. |
| TCP sockets | **No.** Peer is potentially remote; KACS does not capture network identities. `EOPNOTSUPP`. |

A stream or seqpacket socket that is not yet connected fails with `ENOTCONN`. Servers using a transport that does not carry a peer token cannot use `peios_token_impersonate_peer`. They have to obtain a token fd by some other path and use `KACS_IOC_IMPERSONATE` to install it. Common patterns:

- **Token fd passed over the connection.** A datagram protocol can include a token fd in an `SCM_RIGHTS` message; the receiver gets the fd and impersonates from it. The token fd has whatever access the sender opened it with, bounded by what the sender held.
- **Out-of-band capture.** A service that knows the peer's PID can call `kacs_open_process_token(pidfd)` to get the peer's primary token (subject to the process SD and PIP dominance checks). Less common; usually only the loopback-like patterns inside the TCB work this way.

The lack of peer tokens on datagram and pipe transports is intentional, not an oversight. Those transports are fundamentally connection-less or pre-existing; capturing a "peer" identity that may not exist is ill-defined.

## Verifying the server

Capture is symmetric. When the client's `connect()` completes, its own socket's register holds the identity of whoever called `listen()` on the name it reached, at Identification level unless the server raised its listener's level — enough to verify, not enough to impersonate. So a client checks the service it is about to trust with one call:

```c
int server = peios_token_open_peer(sock);   /* who is actually listening */
/* query its user SID, compare with the principal the service is expected to run as */
```

This is what makes a socket path safe to connect to even when the path itself could have been bound by someone else: the name is a rendezvous, the token is the proof. A process that ends up holding a listener it did not create — one returned from peinit's descriptor store after a restart, or one handed over by a broker — calls `peios_socket_restamp` on it before accepting, so that clients see the process actually serving them rather than the one that originally called `listen()`.

## Identity cascading

A service that is impersonating client A may itself need to call a third service. When it does, the connection it opens carries A's identity, not the service's own.

```mermaid
flowchart LR
    A["Client A"] -->|connect| B["Server S1, impersonating A"]
    B -->|connect to S2 while impersonating| C["Server S2"]
    C -.->|peer token sees A, not S1| D["S2 can impersonate A"]
```

The mechanism: the impersonation token is the thread's effective token, and the effective token is what the kernel reads when capturing peer identity at connect. So when S1, while impersonating A, calls `connect()` on a socket to S2, the kernel captures A's identity onto S2's side of the socket. S2 can then call `peios_token_impersonate_peer` and get A.

This cascading is automatic and is what makes the local-IPC ecosystem work cleanly. A user makes one request to a service, and that service makes downstream requests to other services on the user's behalf — registry, file system, audit logging — and each of those downstream services sees the user as the peer. No explicit token forwarding is required.

The cascading is bounded by the impersonation level the original client granted. If A connected at Impersonation level, S1 captures A at Impersonation; when S1 connects to S2, the captured identity on S2's side is bounded by what S1's effective token currently is — which is A at Impersonation. The level does not get re-extended by cascading.

The same mechanism reaches the network boundary only at Delegation. If A connected at Delegation level, the captured identity on cascaded local connections is still A at Delegation, and outbound network calls from S1 carry A's Kerberos credentials (via authd; KACS only records the flag). Without Delegation, network calls from S1 go out as S1, not as A.

## What the server has to do

There are two server-side shapes, depending on which pattern (canonical synchronous or just-in-time) the server is using. Both start at the same point — the kernel has captured the client's peer token onto the socket at connect time — and diverge after accept.

**Canonical synchronous flow** (one OS thread, one request, start to finish):

1. **Accept the connection.** Standard `accept()` on the Unix socket. The kernel has already captured the client's peer token onto this socket.
2. **Impersonate the peer.** Call `peios_token_impersonate_peer(fd)`. The kernel runs the two-gate model and installs the resulting token.
3. **(Optional) Inspect the granted level.** Read the thread's effective token's `impersonation_level`. If it is below what you expected, the client's request, the identity gate, or the integrity ceiling has lowered it.
4. **Do the work.** Every access check on this thread is now against the impersonation token.
5. **Revert.** Call `kacs_revert()`. The thread is back to its primary identity.
6. **Handle the next request.** Either on the same connection (loop back to step 2 if the client may re-impersonate per request) or on the next connection.

**Just-in-time flow** (the right shape for any modern runtime — Go, Rust async, etc. — and the recommended default):

1. **Accept the connection.** As above.
2. **Capture the peer token fd.** Call `peios_token_open_peer(fd)` and store the returned token fd in the request context. The fd carries `TOKEN_QUERY | TOKEN_IMPERSONATE | TOKEN_DUPLICATE`.
3. **(Optional) Inspect the captured token.** Query the captured fd to verify the identity and level before doing any work.
4. **Do most of the request as the service.** Decoding, dispatch, internal bookkeeping, response framing — all run as the service's own identity.
5. **For each access-requiring action**, install the captured token on the current OS thread (`KACS_IOC_IMPERSONATE` on the stored fd), do the single action, call `kacs_revert()` immediately. Keep the impersonation window as tight as possible.
6. **Close the captured fd** at end of request.

A server that handles concurrent connections per thread runs whichever flow it uses in each thread, in parallel. The impersonation state is strictly per-thread; nothing shared.

## Common mistakes

A few patterns that bite first-time service authors:

- **Forgetting to revert.** A thread that finishes a request without calling `kacs_revert` continues to impersonate the previous client. The next request handled on that thread uses the wrong identity. Make `kacs_revert` part of your between-requests cleanup, unconditionally.
- **Reverting too early.** A thread that reverts before all of the work is done — perhaps because an inner function is doing cleanup that runs as the service identity — will fail access checks on the parts that needed to remain impersonated. Keep the impersonation scope wide enough to cover the whole user-facing operation.
- **Holding a peer token fd across exec.** Token fds are file descriptors and survive exec by default (unless O_CLOEXEC was set). But the impersonation state of the thread does not survive exec — it is reverted automatically. If your service execs another binary, the new binary starts with no impersonation, even if the old code was impersonating.
- **Assuming the level you asked for is the level you got.** The two-gate model can silently downgrade. Code that branches on level should query, not assume.

## Where to go next

For what the impersonated identity is checked against once the server starts acting as the client, read [Security descriptors](~peios/security-descriptors/overview).

To drive impersonation from a shell — impersonate a peer, revert, inspect the effective token — read [The token command](~peios/tokens/token-command).

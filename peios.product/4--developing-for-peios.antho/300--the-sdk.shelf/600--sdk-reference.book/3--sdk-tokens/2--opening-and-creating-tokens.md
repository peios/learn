---
title: Opening and creating tokens
description: The entry points that hand back a token fd — opening your own, another process's, or minting a new one.
---

Each of these returns a token fd (or `-1` with `errno`).

```c
int peios_token_open_self(unsigned flags, uint32_t access);
int peios_token_open_process(int pidfd, uint32_t access);
int peios_token_open_thread(int pidfd, int tid, uint32_t access);
int peios_token_open_peer(int conn_fd);
int peios_token_create_raw(const void *spec, size_t len);
```

| Function | Opens |
|---|---|
| `peios_token_open_self` | The calling thread's token. `flags` may be `KACS_TOKEN_OPEN_REAL` to get the **primary** token even while the thread is impersonating; otherwise you get the effective (impersonation-aware) token. `access` is the desired handle rights. |
| `peios_token_open_process` | The **primary** token of the process named by `pidfd`. Subject to a process-query access check and PIP dominance over the target. |
| `peios_token_open_thread` | Thread `tid`'s **impersonation** token if it is impersonating, else the process primary token. |
| `peios_token_open_peer` | The peer-identity token captured at `connect()` on a connected Unix stream/seqpacket socket `conn_fd` — how a server learns *who* is on the other end of a socket. Reads the `KACS_SO_PEER_TOKEN` socket option (level `SOL_KACS`, `<pkm/socket.h>`). The handle carries fixed `QUERY | IMPERSONATE` rights (no `access` argument). |
| `peios_token_create_raw` | Mints a token from a pre-built token-spec buffer. This is the escape hatch — **prefer the builder below**. Requires `SeCreateTokenPrivilege`. |

Errors, per call:

- **`peios_token_open_self`** — `EINVAL` (unknown `flags`; empty or unknown `access` bits), `EACCES` (the token's own SD denies `access`).
- **`peios_token_open_process`** — `EACCES` (any of the three checks failed — process-query right, PIP dominance, or the token SD; deliberately indistinguishable), `EBADF` (invalid pidfd), `ESRCH` (target exited), `EINVAL` (empty or unknown `access` bits).
- **`peios_token_open_thread`** — the `_open_process` set, plus `ESRCH` (thread exited, or not in `pidfd`'s process) and `EINVAL` (`tid <= 0`).
- **`peios_token_open_peer`** — `ENOTCONN` (not connected), `ENODATA` (connected but no captured identity — a socketpair end), `EOPNOTSUPP` (a datagram or non-Unix socket), `ENOTSOCK` (not a socket), `EBADF` (invalid fd).
- **`peios_token_create_raw`** — `EPERM` (privilege missing), `EINVAL` (spec failed kernel validation), `EFAULT` (bad spec pointer), `ENOMEM` (allocation failed).

`peios_token_open_peer` is the cornerstone of local authentication: accept a connection, open the peer token, and you have the caller's identity to query or impersonate — no password, no handshake, just the kernel's word for who connected.

## Peer identity on sockets

```c
int peios_token_impersonate_peer(int conn_fd);
int peios_socket_set_impersonation_level(int sock_fd, uint32_t level);
int peios_socket_get_impersonation_level(int sock_fd, uint32_t *level);
int peios_socket_set_pass_token(int sock_fd, bool on);
```

- `peios_token_impersonate_peer` is `peios_token_open_peer` followed by `peios_token_impersonate` and a `close` — the one-call form for a handler that impersonates, works, and reverts on a single thread. It returns 0 or -1; the errno is whichever step failed.
- `peios_socket_set_impersonation_level` is the **client's** side of the exchange: it sets the `KACS_SO_IMPERSONATION_LEVEL` socket option (`KACS_IMLEVEL_*`), bounding the level at which the peer may capture this socket's identity — Identification to be known but not acted as, Anonymous to withhold identity entirely. Usually set before `connect()`; it may change at any time and bounds every capture from then on. The default is `KACS_IMLEVEL_IMPERSONATION`. Errors: `EINVAL` (unknown level), `EOPNOTSUPP` (a non-Unix socket).
- `peios_socket_get_impersonation_level` reads the level back into `*level`.
- `peios_socket_set_pass_token` turns on per-message identity for a sending socket (`KACS_SO_PASS_TOKEN`): every send then carries the sender's effective identity as a `KACS_SCM_TOKEN` ancillary message, and the peer's `peios_token_open_peer` follows whoever was impersonating at each send. This is what makes a pooled or multiplexed connection convey the right identity per request without the client library knowing. To attach a *specific* token to one message instead — a router forwarding for many clients — send a `KACS_SCM_TOKEN` cmsg (level `SOL_KACS`, data: the token fd) on `sendmsg`; the kernel gates it as if you were impersonating that token and fails with `EPERM` rather than downgrading.

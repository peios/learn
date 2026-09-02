---
title: Socket Identity
description: The governing identity KACS stamps on every inet socket for network policy — which token, taken when, and how the engine reads it.
---

Network policy speaks of programs, and a packet carries no program. What
carries one is the socket: KACS records on every `AF_INET` and
`AF_INET6` socket the **identity that governs its traffic**, and the
network policy engine (Chapter 6, §6.9) reads it at the first judgment
of each flow. AF_UNIX sockets carry the peer-identity machinery of
§3.12.1 instead and are not stamped.

## The stamp

The stamp is the caller's **effective token** — the impersonation token
during impersonation, the primary otherwise — held by a counted
reference, together with the process facts of that moment: the process
GUID (§3.3.2), the thread-group id, and the task's `comm`. Choosing the
effective token means a service thread acting for a client attributes
the socket to the client, exactly as file creation and audit do under
impersonation; the service's own identity is then not on the socket for
that flow.

It is taken at every act that commits the socket to a role, and the
last one governs:

| Act | Where |
|---|---|
| creation | `socket_post_create`; a kernel socket (`sock_create_kern`) is stamped as the **kernel's**, with no token |
| `bind(2)` | after the port reservation permits it (§3.12.1) |
| `listen(2)` | `socket_listen` |
| `connect(2)` | `socket_connect` |
| `accept(2)` | `sk_clone_security`: the child inherits the listener's stamp, its own reference |
| `KACS_SO_RESTAMP` | any state: the caller's effective identity replaces the stamp |

Restamping is what makes a hand-off well defined. A listener opened by
one program and passed to another — socket activation, a descriptor
store, a broker — is governed by whichever program last committed it,
and a program that receives a socket it did not create can say so
explicitly with `KACS_SO_RESTAMP`, self-gated like every attestation of
one's own identity. Sockets that never pass through these hooks (a task
with no token in early boot) read as *unstamped*, which the engine
treats as the kernel's and confesses.

## Reading it

The engine reads the stamp with `pkm_kacs_socket_owner()`
(`<linux/peios_pnp.h>`): a counted token reference the caller releases
with `pkm_kacs_socket_owner_put()`, and a copy of the kind, GUID, pid and
comm. The copy is what makes the facts outlive the process; the
reference is what makes them outlive the socket — a flow keeps its
identity for its life (§6.9) even after the socket that started it is
gone. The fields live under their own lock, taken with bottom halves
disabled, because both the accept path and the engine's read run in
softirq context.

## Tracing

Every stamp emits `kacs:kacs_socket_token` with reason `owner`; the
`max_imp` field carries the kind (1 program, 2 kernel). See Appendix
3.C.

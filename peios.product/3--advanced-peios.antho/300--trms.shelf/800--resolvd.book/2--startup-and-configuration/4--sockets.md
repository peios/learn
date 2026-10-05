---
title: Sockets and Descriptors
description: The native socket and its directory and their descriptors, the stub listener's sockets, and every other descriptor resolvd holds.
---

## The native socket

The native door is a `SOCK_STREAM` Unix socket at
`/run/resolvd/resolv.sock` (PSPU §6.4), inside resolvd's runtime
directory rather than directly in `/run`, which resolvd's account cannot
write.

At startup resolvd:

1. creates `/run/resolvd` if peinit has not, and sets its mode to
   `0755`; [*sockets.runtime-directory-mode-0755]
2. replaces the directory's DACL (below);
3. removes any existing `/run/resolvd/resolv.sock`, logging
   `removed a stale /run/resolvd/resolv.sock` when there was one; [*sockets.stale-socket-removed-and-logged]
4. binds the socket, sets its mode to `0666`, and replaces its DACL in
   the same way; [*sockets.socket-mode-0666]
5. makes the listener nonblocking.

The DACL written to both the directory and the socket is: [*sockets.directory-and-socket-dacl]

| Trustee | Access |
|---|---|
| SYSTEM | `GENERIC_ALL` |
| Everyone | `GENERIC_READ`, `GENERIC_WRITE`, `GENERIC_EXECUTE` |

Only the DACL is written; the owner stays resolvd's account, which
created both objects. [*sockets.owner-left-as-resolvd] Reaching the socket grants nothing: every request
is checked against the control object (§5.2).

If the descriptor cannot be written, resolvd logs at error level

```text
could not set a descriptor on <path> (<error>); programs other than SYSTEM and administrators will not be able to reach the socket
```

and carries on. [*sockets.descriptor-failure-logged-not-fatal] The socket then keeps whatever descriptor it was
created with, and for ordinary processes the native door — and with it
the NSS shim — is unreachable while the stub listener still works
(§9.3).

## The stub listener

Two sockets, a UDP socket and a TCP listener, both bound to
`127.0.0.53` port 53 and both nonblocking (PSPU §6.8). [*sockets.stub-udp-and-tcp-on-127-0-0-53] Nothing is bound
on `::1` or on any other address. [*sockets.nothing-bound-on-other-addresses] Binding port 53 depends on the port
reservation (§2.1).

## Other descriptors

| Descriptor | Count | Lifetime |
|---|---|---|
| The registry watch on `Machine\System\Network` | 0 or 1 | From startup; replaced on a watch error (§2.3) |
| The netd channel | 0 or 1 | While subscribed (§3.1) |
| Native connections still sending a request | up to 256 | Until the request is complete, or 5 s (§5.1) |
| Stub TCP connections still sending a query | up to 256 | Until the query is complete, or 10 s (§6.1) |
| Native and stub TCP connections awaiting an answer | not bounded separately | Until the engine answers |
| Upstream sockets | one per transaction, up to the in-flight ceiling and its retries | One transaction (§4.7) |

A connection whose request has been read is no longer counted against
the 256. It is held until its question is answered, which is bounded by
the engine's own timeouts (§4.6), not by a count. [*sockets.answered-connections-not-counted]

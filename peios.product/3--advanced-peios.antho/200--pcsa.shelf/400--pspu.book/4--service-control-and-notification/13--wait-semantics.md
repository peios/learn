---
title: Wait Semantics
description: What ending a wait means, and how the wait flag changes when a lifecycle command responds.
---

`wait` decides whether a lifecycle command's response is sent
immediately or held until the operation resolves.

With `wait: false`, the manager MUST respond as soon as it has accepted
the operation, with the acknowledgement shape and the service's state at
that moment.

With `wait: true`, the manager MUST hold the connection open and respond
when the operation reaches a terminal state, with the same shape and the
service's state, cause and warnings observed at that time.

A connection blocked on a wait is not idle (§4.4). The manager MUST NOT
close it for idleness however long the operation runs.

## When a wait ends

| Ending | Response |
|---|---|
| The operation reaches a terminal state | The acknowledgement shape. |
| The operation's lifetime expires | `OPERATION_TIMEOUT`. |
| The operation is no longer held by the manager | `UNKNOWN_OPERATION`. |

`OPERATION_TIMEOUT` ends the client's wait, not the operation. The
operation continues, and the client MAY still observe it with
`operation-status` using the identifier it never received — which it
does not have. A client that needs to survive a timeout SHOULD issue the
command with `wait: false`, keep the identifier, and poll.

## Reload mode

A response to a `reload` command MUST carry a `mode` field saying how
the reload resolved:

| Value | Meaning |
|---|---|
| `confirmed` | The service acknowledged the reload by signalling readiness. The reload demonstrably happened. |
| `advisory` | The manager issued the reload and the service did not acknowledge it. The reload probably happened; nothing confirms it. |
| `failed` | The reload did not happen. An external reload command exited non-zero or timed out. |

`mode` MUST be present on every response to a `reload`, including one
sent with `wait: false` — in which case it MUST be `advisory`, since
nothing has been observed yet.

A client MUST treat these three as an exhaustive set and MUST NOT expect
a fourth. A manager MUST NOT introduce one without §4.21.

The distinction between `confirmed` and `advisory` is the whole value of
the field: a service that implements the reload handshake (§4.19) can be
*known* to have reloaded, and one that does not cannot. `failed` does
not mean the service stopped — a failed reload leaves a running service
running.

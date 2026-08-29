---
title: Limits and Defaults
description: The limits and defaults a Peios service manager uses on both channels, and which of them are configurable.
---

The values a Peios service manager uses. A manager MAY use different
ones; where a value is configurable, it MUST be discoverable to an
administrator through the same surface that sets it.

## Control channel

| Bound | Value | Configurable | Defined in |
|---|---|---|---|
| Socket path | `/run/services/peinit/control.sock` | No | §4.4 |
| Concurrent connections | 32 | Yes | §4.4 |
| Request size | 65536 bytes, excluding the terminating newline | Yes | §4.4 |
| Idle timeout | 30 seconds | Yes | §4.4 |
| Listen backlog | 32 | No | §4.4 |

## Operations

| Bound | Value | Defined in |
|---|---|---|
| Terminal record retention | 60 seconds | §4.14 |
| Operation lifetime | The target service's own start or stop timeout | §4.11 |

## Notification channel

| Bound | Value | Defined in |
|---|---|---|
| Maximum datagram | 65536 bytes | §4.16 |
| Descriptors per datagram | 64 | §4.16 |
| First returned descriptor | 3 | §4.20 |
| Descriptor store maximum | Per service; 0 disables | §4.20 |
| Timeout extension cap | 4 × the phase's base timeout | §4.19 |
| Progress event rate | At most one per sender per second | §4.19 |

## Composing the two channels

A `STATUS` value a service sends on the notification channel is
returned as `status_text` on the control channel. The notification
datagram bound is 65536 bytes and the control response is not bounded by
the request limit, so a status string that fits in a datagram is always
returnable.

The bounds are stated at their values here rather than left to each
implementation because a producer has no other way to learn them.
Lowering either without telling anyone breaks every service that was
sizing to the old one, and the failure — a truncated datagram, or a
connection closed mid-request — does not name its cause.

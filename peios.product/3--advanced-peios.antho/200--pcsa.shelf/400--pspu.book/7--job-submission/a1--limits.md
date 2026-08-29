---
title: Limits and Defaults
description: The limits and defaults a Peios service manager uses on the jobs channel, and which of them are configurable.
---

The values a Peios service manager uses. A manager MAY use different
ones; where a value is configurable, it MUST be discoverable to an
administrator through the same surface that sets it.

## The socket

| Bound | Value | Configurable | Defined in |
|---|---|---|---|
| Socket path | `/run/services/peinit/jobs.sock` | No | §7.3 |
| Socket descriptor, default | Connect for Authenticated Users (`S-1-5-11`); full control for SYSTEM and Administrators | Yes | §7.3 |
| Concurrent connections | 64 | Yes | §7.3 |
| Message size | 65536 bytes | Yes | §7.3 |
| Idle timeout | 30 seconds | Yes | §7.3 |
| Listen backlog | 32 | No | §7.3 |
| Live jobs per submitter | 64; SYSTEM exempt | Yes | §7.3 |

## Attachments

| Bound | Value | Defined in |
|---|---|---|
| Tokens per message | 1 | §7.4 |
| Descriptors per message | 64, including an output sink | §7.4 |
| First injected descriptor | 3 | §7.9 |

## The definition

| Field | Default | Defined in |
|---|---|---|
| `stop_timeout` | 10 seconds | §7.6 |
| `readiness_timeout` | 30 seconds | §7.6 |
| `timeout` | 0, no limit | §7.6 |
| `working_directory` | `/` | §7.6 |

## Records

| Bound | Value | Defined in |
|---|---|---|
| Terminal record retention | 60 seconds | §7.7 |

The retention value is the control channel's operation retention
(§4.A), for the same reason: a client polling once a second must never
find the outcome gone.

## Composing with the control channel

A job's `status_text` and `progress` come from datagrams on the
notification channel, whose bound is §4.A's 65536 bytes; the job view
is not bounded by the jobs channel's message size on the way out, so
a status a job can send is always one the manager can return.

The message-size bound applies to a `submit` and therefore to the sum
of its definition: a program with a very large `environment` or
`arguments` list is bounded here before it is bounded by `execve`.

---
title: Operation Events
description: The seven operation lifecycle events, the five fields they share, what duration_ns measures from, and the one field that goes by three names.
---

Every operation event carries the same five fields: `operation_id`,
`type`, `service`, `source`, `caller` — `null` for a
lifecycle-generated operation — and `state` after the transition.

Seven types, each adding its own fields:

| Event | Adds |
|---|---|
| `operation.requested` | — |
| `operation.started` | — |
| `operation.completed` | `duration_ns`, `result` |
| `operation.failed` | `duration_ns`, `failure_reason` |
| `operation.cancelled` | `reason` |
| `operation.merged` | `merged_into` |
| `operation.aborted` | `duration_ns`, `reason` |

## duration_ns measures from creation

Not from the start of execution. The reasoning is the same as for the
operation timeout: what a caller waited is what matters, and queue time
is part of it.

An operation that sat in a queue for a minute and then ran for a second
reports 61 seconds, not 1.

## One field, three names

The same value appears under three spellings across two surfaces:

- `failure_reason` on `operation.failed`
- `reason` on `operation.cancelled` and `operation.aborted`
- `error` in the control interface's operation view (PSPU §4)

A consumer correlating an event stream against the control interface has
to map all three onto each other.

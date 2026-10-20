---
title: Wire Vocabulary
description: Every enumerated value on the jobs channel — commands, job state, cause, readiness, wait condition and progress unit.
---

Every enumerated value that appears on the jobs channel. All are lower
snake case. A manager MUST NOT emit a value outside these sets without
the negotiation in §4.21, and a submitter MUST treat one it does not
recognise as an error for that request rather than mapping it onto a
value it knows.

Values shared with the control channel — response status, job type —
are §4.B's and are not restated.

## Command

`submit`, `status`, `wait`, `stop`, `signal`

## Job state

| Value | Process? | Terminal? |
|---|---|---|
| `created` | Not yet | No |
| `running` | Yes | No |
| `completed` | No | Yes |
| `failed` | No | Yes |
| `abandoned` | Yes, unkillably | Yes |

`created` is never reported on this channel (§7.6). It appears here
because the control channel's `job-list` may show it for a job whose
submit is still in flight.

## Cause

`parent_setup_failure`, `pre_exec_failure`, `readiness_timeout`,
`timeout`, `explicit_stop`, `shutdown`, `process_unkillable`

`cause` is null when the process ended of its own accord.

## Readiness

`none`, `notify`

Request-only, on `submit`. The job view reports readiness through
`ready`, not by echoing this.

## Wait condition

`terminal`, `ready`

Request-only, the `for` field of `wait`.

## Progress unit

`bytes`, `items`, `percent`

The vocabulary of `PROGRESS_UNIT` (§4.19), reported in the job view's
`progress.unit`. Null when the job sent none.

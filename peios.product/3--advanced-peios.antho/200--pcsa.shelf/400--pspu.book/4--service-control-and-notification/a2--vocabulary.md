---
title: Wire Vocabulary
description: Every enumerated value on the control channel — response status, service state, transition cause, health, job and operation types.
---

Every enumerated value that appears on the control channel. All are
lower snake case. A manager MUST NOT emit a value outside these sets
without the version negotiation in §4.21, and a client MUST treat one it
does not recognise as an error for that request rather than mapping it
onto a value it knows.

## Response status

`ok`, `error`

## Service state

| Value | Process? | Satisfies dependents? |
|---|---|---|
| `inactive` | No | No |
| `starting` | Maybe | No |
| `active` | Yes | Yes |
| `reloading` | Yes | Yes |
| `stopping` | Briefly | No |
| `completed` | No | Yes |
| `backoff` | No | No |
| `failed` | No | No |
| `abandoned` | Yes, unkillably | No |
| `skipped` | No | Yes |

Exactly three states satisfy dependents: `active`, `completed` and
`skipped`. A client deciding whether something depending on this service
could be running MUST use that set and no other.

## Transition cause

`explicit_start`, `dependency_start`, `restart_policy`,
`binds_to_recovery`, `timer`, `explicit_stop`, `explicit_reload`,
`explicit_reset`, `conflict_eviction`, `binds_to_propagation`,
`shutdown_wave`, `process_crash`, `clean_exit`, `clean_exit_restart`,
`readiness_timeout`, `watchdog_timeout`, `health_check_failure`,
`pre_hook_failure`, `parent_setup_failure`, `pre_exec_failure`,
`dependency_failure`, `restart_budget_exhausted`, `cycle_detected`,
`validation_error`, `assertion_error`, `condition_skipped`,
`process_unkillable`

A `cause` may also be `null`, for a service that has not transitioned.

## Service health

`healthy`, `unhealthy`, `unknown`

`health` is `null` when the service has no health check configured,
which is distinct from `unknown` — the latter means one is configured
and has not produced a result yet.

## Job type

`service_main`, `pre_exec_hook`, `post_exec_hook`, `reload_hook`,
`health_check`, `submitted`

Only `service_main` appears in `current_job`. Only `submitted` appears
in a job view (§7.7); a job's state and cause vocabularies are §7.B's.

## Operation type

`start`, `stop`, `restart`, `reload`, `reset`

## Operation state

| Value | Terminal? | Meaning |
|---|---|---|
| `pending` | No | Queued, not yet executing. |
| `running` | No | Executing. |
| `completed` | Yes | Reached its goal. |
| `failed` | Yes | Did not reach its goal, or expired while queued. |
| `merged` | Yes | Merged into another operation. |
| `cancelled` | Yes | Terminated while pending. Never executed. |
| `aborted` | Yes | Terminated while running. |

## Operation source

`admin`, `boot`, `shutdown`, `dependency_propagation`, `restart_policy`,
`timer`, `binds_to_recovery`, `binds_to_propagation`,
`conflict_resolution`, `on_failure`

`admin` is the only source a client's own command produces. The rest
describe operations the manager created for its own reasons, and a
client observing one has learned something about what the manager is
doing rather than about anything it asked for.

## Reload mode

`confirmed`, `advisory`, `failed`

## Status warning type

`service_tree`, `health`, `hooks`

These name what part of a service's process containment could not be
reclaimed, `service_tree` being the whole of it and therefore the most
serious. A client MUST accept a value outside this set and MUST NOT
discard the warning (§4.21).

## Shutdown type

`poweroff`, `reboot`, `halt`

Request-only; the manager does not echo it.

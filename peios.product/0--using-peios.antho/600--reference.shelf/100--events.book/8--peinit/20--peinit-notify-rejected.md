---
title: "peinit.notify.rejected"
description: "peinit refused a datagram on the notification channel and applied none of it: the sender could not be authenticated, the message did not parse, or it made no sense for the job's state."
---

- **Event type:** `peinit.notify.rejected`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every refused notification datagram is recorded
- **Cardinality:** one record per occurrence

peinit refused a datagram on the notification channel and applied none of
it: the sender could not be authenticated, the message did not parse, or
it made no sense for the job's state. A stream of these from one process
is worth reading.

Formerly `notify.rejected`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | Why the datagram was refused. `internal-error` is peinit unable to act on it, not anything wrong with the datagram; `shutdown-refused` is a timeout extension (`EXTEND_TIMEOUT_USEC=`) the shutdown in progress would not grant.<br><br>Values here (open set): `invalid-utf8` · `malformed-line` · `truncated` · `unauthenticated-sender` · `missing-service` · `job-not-running` · `missing-process` · `pidfd-mismatch` · `process-verification-failed` · `generation-mismatch` · `missing-start-operation` · `missing-reload-operation` · `unsupported-reload-operation` · `unsupported-ready-state` · `shutdown-refused` · `internal-error`. |
| [`subject.process.pid`](~peios/events/field-index/fields-subject#subject.process.pid) | `uint` | optional | The sending process, when the kernel gave its credentials. |
| [`subject.service.name`](~peios/events/field-index/fields-subject#subject.service.name) | `str` | optional | The sender's service, when peinit could attribute it. |
| [`subject.job.guid`](~peios/events/field-index/fields-subject#subject.job.guid) | `bin.guid` | optional | The job whose process sent a notification message: the service's main process, or a submitted job. |
| [`subject.job.activation-generation`](~peios/events/field-index/fields-subject#subject.job.activation-generation) | `uint` | optional | The activation generation of the service whose job sent a notification message, as `object.job.activation-generation` describes it. |
| [`subject.operation.guid`](~peios/events/field-index/fields-subject#subject.operation.guid) | `bin.guid` | optional | The peinit operation the sending job was serving when it sent a notification message, such as the start that a readiness message completes. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

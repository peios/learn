---
title: "peinit.notify.progress.reported"
description: "A service's job sent PROGRESS= or PROGRESS_UNIT=, and this is the progress peinit retained after it."
---

- **Event type:** `peinit.notify.progress.reported`
- **Defined in:** `peinit.evman`
- **Tier:** verbose
- **Gating:** none — every change of progress is recorded, within the rate bound
- **Cardinality:** at most one per service activation per second

A service's job sent `PROGRESS=` or `PROGRESS_UNIT=`, and this is the
progress peinit retained after it.

Formerly `notify.progress`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.service.name`](~peios/events/field-index/fields-subject#subject.service.name) | `str` | required | The service whose job sent a notification message. |
| [`subject.job.guid`](~peios/events/field-index/fields-subject#subject.job.guid) | `bin.guid` | required | The job whose process sent a notification message: the service's main process, or a submitted job. |
| [`subject.job.activation-generation`](~peios/events/field-index/fields-subject#subject.job.activation-generation) | `uint` | required | The activation generation of the service whose job sent a notification message, as `object.job.activation-generation` describes it. |
| [`subject.operation.guid`](~peios/events/field-index/fields-subject#subject.operation.guid) | `bin.guid` | optional | The peinit operation the sending job was serving when it sent a notification message, such as the start that a readiness message completes. |
| [`notify.progress.current`](~peios/events/field-index/fields-notify#notify.progress.current) | `uint` | optional | How far a service or submitted job has got, as it reported with `PROGRESS=`: the count before any `/`. |
| [`notify.progress.total`](~peios/events/field-index/fields-notify#notify.progress.total) | `uint` | optional | The end `notify.progress.current` is counting towards, as reported after the `/` of `PROGRESS=`. |
| [`notify.progress.bounded`](~peios/events/field-index/fields-notify#notify.progress.bounded) | `bool` | optional | Whether the progress a service or submitted job reported declares an end: true for `PROGRESS=N/` and `PROGRESS=N/M`, false for a bare `PROGRESS=N`, which counts with no end (PSPU <span>§</span>4.19). |
| [`notify.progress.unit`](~peios/events/field-index/fields-notify#notify.progress.unit) | `str.enum` | optional | What `notify.progress.current` and `notify.progress.total` count, as reported with `PROGRESS_UNIT=`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

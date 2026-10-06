---
title: "peinit.job.status.reported"
description: "A submitted job reported STATUS= or PROGRESS= on the notification channel, and this is what peinit retained after it."
---

- **Event type:** `peinit.job.status.reported`
- **Defined in:** `peinit.evman`
- **Tier:** verbose
- **Gating:** none — every change a submitted job reports is recorded, within the rate bound
- **Cardinality:** at most one per job per second; a report inside the window updates the job view and writes nothing

A submitted job reported `STATUS=` or `PROGRESS=` on the notification
channel, and this is what peinit retained after it.

Formerly `job.status`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.job.guid`](~peios/events/field-index/fields-object#object.job.guid) | `bin.guid` | required | The job the event is about. |
| [`object.job.submitter.sid`](~peios/events/field-index/fields-object#object.job.submitter.sid) | `bin.sid` | required | The user SID of the client that submitted the job. |
| [`notify.status`](~peios/events/field-index/fields-notify#notify.status) | `str` | optional | The text a service sent as `STATUS=`: free text describing what it is doing. |
| [`notify.progress.current`](~peios/events/field-index/fields-notify#notify.progress.current) | `uint` | optional | How far a service or submitted job has got, as it reported with `PROGRESS=`: the count before any `/`. |
| [`notify.progress.total`](~peios/events/field-index/fields-notify#notify.progress.total) | `uint` | optional | The end `notify.progress.current` is counting towards, as reported after the `/` of `PROGRESS=`. |
| [`notify.progress.bounded`](~peios/events/field-index/fields-notify#notify.progress.bounded) | `bool` | optional | Whether the progress a service or submitted job reported declares an end: true for `PROGRESS=N/` and `PROGRESS=N/M`, false for a bare `PROGRESS=N`, which counts with no end (PSPU <span>§</span>4.19). |
| [`notify.progress.unit`](~peios/events/field-index/fields-notify#notify.progress.unit) | `str.enum` | optional | What `notify.progress.current` and `notify.progress.total` count, as reported with `PROGRESS_UNIT=`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

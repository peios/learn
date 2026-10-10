---
title: "peinit.notify.errno.reported"
description: "A service's job sent ERRNO=: its own claim about an error, which peinit neither acts on nor retains."
---

- **Event type:** `peinit.notify.errno.reported`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every authenticated `ERRNO=` is recorded
- **Cardinality:** one record per occurrence

A service's job sent `ERRNO=`: its own claim about an error, which peinit
neither acts on nor retains.

Formerly `notify.errno`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.service.name`](~peios/events/field-index/fields-subject#subject.service.name) | `str` | required | The service whose job sent a notification message. |
| [`subject.job.guid`](~peios/events/field-index/fields-subject#subject.job.guid) | `bin.guid` | required | The job whose process sent a notification message: the service's main process, or a submitted job. |
| [`subject.job.activation-generation`](~peios/events/field-index/fields-subject#subject.job.activation-generation) | `uint` | required | The activation generation of the service whose job sent a notification message, as `object.job.activation-generation` describes it. |
| [`subject.operation.guid`](~peios/events/field-index/fields-subject#subject.operation.guid) | `bin.guid` | optional | The peinit operation the sending job was serving when it sent a notification message, such as the start that a readiness message completes. |
| [`notify.errno`](~peios/events/field-index/fields-notify#notify.errno) | `int.errno` | optional | Absent when the text sent was not a positive number. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

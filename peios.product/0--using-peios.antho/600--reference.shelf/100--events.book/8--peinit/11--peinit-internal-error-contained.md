---
title: "peinit.internal-error.contained"
description: "peinit could not carry out a step on a service's behalf, and contained the fault to that service."
---

- **Event type:** `peinit.internal-error.contained`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every contained internal error is recorded
- **Cardinality:** one record per occurrence

peinit could not carry out a step on a service's behalf, and contained the
fault to that service. The fault is peinit's, not the service's; the job,
operation and state change it caused have their own events.

The error itself is not carried: every path that contains one has it only
as Rust Debug output, which no event field admits. peinit's console line
and the failed operation's result keep it.

Formerly `service.internal_error`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`operation.stage`](~peios/events/field-index/fields-operation#operation.stage) | `str.enum` | required | The step peinit could not carry out.<br><br>Values here (open set): `job-terminal` · `process-setup` · `lifecycle-deadline` · `notify`. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | optional | The name of the service the event is about, as its definition names it. |
| [`object.job.guid`](~peios/events/field-index/fields-object#object.job.guid) | `bin.guid` | optional | The job the event is about. |
| [`object.service.failed`](~peios/events/field-index/fields-object#object.service.failed) | `bool` | optional | Present exactly when `object.service.name` is. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

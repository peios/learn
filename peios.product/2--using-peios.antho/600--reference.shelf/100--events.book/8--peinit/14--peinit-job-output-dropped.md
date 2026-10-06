---
title: "peinit.job.output.dropped"
description: "A submitted job's submitter stopped draining its output, and peinit began dropping the submitter's copy of the job's lines."
---

- **Event type:** `peinit.job.output.dropped`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none
- **Cardinality:** once per job, on the first line dropped

A submitted job's submitter stopped draining its output, and peinit began
dropping the submitter's copy of the job's lines. The copy sent to the log
store is unaffected.

Formerly `output.dropped`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.job.guid`](~peios/events/field-index/fields-object#object.job.guid) | `bin.guid` | required | The job the event is about. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

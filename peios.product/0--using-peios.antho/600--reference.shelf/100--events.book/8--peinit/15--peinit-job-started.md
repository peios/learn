---
title: "peinit.job.started"
description: "A job's process exists and has been executed: the moment a process is running as object.job.token.sid on peinit's behalf."
---

- **Event type:** `peinit.job.started`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every job whose process starts is recorded
- **Cardinality:** one record per occurrence

A job's process exists and has been executed: the moment a process is
running as `object.job.token.sid` on peinit's behalf.

Formerly `job.started`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.job.guid`](~peios/events/field-index/fields-object#object.job.guid) | `bin.guid` | required | The job the event is about. |
| [`object.job.type`](~peios/events/field-index/fields-object#object.job.type) | `str.enum` | required | What the job is for. |
| [`object.job.state`](~peios/events/field-index/fields-object#object.job.state) | `str.enum` | required | Always `running`. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | when `object.job.type != submitted` | The name of the service the event is about, as its definition names it. |
| [`object.job.activation-generation`](~peios/events/field-index/fields-object#object.job.activation-generation) | `uint` | when `object.job.type != submitted` | The activation generation of the service the job belongs to, at the time the job was created. |
| [`object.operation.guid`](~peios/events/field-index/fields-object#object.operation.guid) | `bin.guid` | optional | The peinit operation the event is about: a start, stop, restart, reload or reset of one service, from the moment it is requested to the moment it ends. |
| [`object.process.pid`](~peios/events/field-index/fields-object#object.process.pid) | `uint` | required | The job's process. |
| [`object.cgroup.path`](~peios/events/field-index/fields-object#object.cgroup.path) | `str.path` | required | The cgroup the job's process runs in. |
| [`object.job.token.sid`](~peios/events/field-index/fields-object#object.job.token.sid) | `bin.sid` | required | The user SID of the token the job's process runs as. |
| [`object.job.token.groups`](~peios/events/field-index/fields-object#object.job.token.groups) | `bin.sid[]` | required | The group SIDs of the token the job's process runs as, in the token's order. |
| [`object.job.token.privileges`](~peios/events/field-index/fields-object#object.job.token.privileges) | `uint.flags` | required | The privileges present on the token the job's process runs as, as the flags of the 64-bit privilege word of `uapi/pkm/token.h`, one `KACS_SE_*_PRIVILEGE` bit each. |
| [`object.job.token.privileges-enabled`](~peios/events/field-index/fields-object#object.job.token.privileges-enabled) | `uint.flags` | required | Which of the privileges in `object.job.token.privileges` are enabled, as flags in the same 64-bit word. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

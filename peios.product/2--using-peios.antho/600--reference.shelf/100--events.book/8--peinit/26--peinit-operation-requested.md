---
title: "peinit.operation.requested"
description: "An operation on a service — a start, stop, restart, reload or reset — was created."
---

- **Event type:** `peinit.operation.requested`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every operation is recorded
- **Cardinality:** one record per occurrence

An operation on a service — a start, stop, restart, reload or reset — was
created. A client's command creates one with `object.operation.source`
`admin`; every other source is peinit acting for its own reasons. Every
operation in a graph context is requested when the context is built.

Formerly `operation.requested`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.operation.guid`](~peios/events/field-index/fields-object#object.operation.guid) | `bin.guid` | required | The peinit operation the event is about: a start, stop, restart, reload or reset of one service, from the moment it is requested to the moment it ends. |
| [`object.operation.type`](~peios/events/field-index/fields-object#object.operation.type) | `str.enum` | required | What the operation does to its service. |
| [`object.operation.source`](~peios/events/field-index/fields-object#object.operation.source) | `str.enum` | required | Who or what asked for the operation. |
| [`object.operation.state`](~peios/events/field-index/fields-object#object.operation.state) | `str.enum` | required | Always `pending`. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | required | The name of the service the event is about, as its definition names it. |
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | optional | The client whose command created the operation. Absent for an operation peinit created itself. |
| [`subject.token.groups`](~peios/events/field-index/fields-subject#subject.token.groups) | `bin.sid[]` | optional | Written only when peinit holds the client's whole token. For a control-channel caller it holds the user SID alone, so today an operation's subject is `subject.token.sid` and nothing more. |
| [`subject.token.privileges`](~peios/events/field-index/fields-subject#subject.token.privileges) | `uint.flags` | optional | Present exactly when `subject.token.groups` is. |
| [`subject.token.privileges-enabled`](~peios/events/field-index/fields-subject#subject.token.privileges-enabled) | `uint.flags` | optional | Present exactly when `subject.token.groups` is. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

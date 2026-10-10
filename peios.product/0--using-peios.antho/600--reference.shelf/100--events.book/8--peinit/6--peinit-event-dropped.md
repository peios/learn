---
title: "peinit.event.dropped"
description: "The ring refused one of peinit's events, and it is gone."
---

- **Event type:** `peinit.event.dropped`
- **Defined in:** `peinit.evman`
- **Tier:** essential
- **Gating:** none
- **Cardinality:** once per event the ring refused

The ring refused one of peinit's events, and it is gone. Written so that
the trail records the gap rather than, for example, a job with a
`peinit.job.started` and no `peinit.job.ended`. Small by construction, and
if the ring refuses this one too peinit treats it as fatal. Essential
because it is the record of a hole in the audit trail.

There is no count of drops on the record: count the records. The
`truncated` notice that used to follow a cut `job.ended` is gone, because
`peinit.job.ended` says itself when its arguments were cut.

Formerly `event.oversized`, with action `dropped`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`emission.type`](~peios/events/field-index/fields-emission#emission.type) | `str` | required | The event type an emitter was trying to emit, as it supplied it. |
| [`emission.payload-length`](~peios/events/field-index/fields-emission#emission.payload-length) | `uint.bytes` | required | The byte length of an event's MessagePack payload, without the header or the event type. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | optional | The service the refused event was about, or whose job sent it. |
| [`object.job.guid`](~peios/events/field-index/fields-object#object.job.guid) | `bin.guid` | optional | The job the refused event was about, or whose process sent it. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | optional | The error the emit returned, where it gave a number. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

---
title: "eventd.events.lost"
description: "The record that eventd found events missing from a CPU's ring: sequence numbers it never read and never stored."
---

- **Event type:** `eventd.events.lost`
- **Defined in:** `eventd.evman`
- **Tier:** essential
- **Gating:** none — every gap found is recorded
- **Cardinality:** once per contiguous run of missing sequence numbers on one ring

The record that eventd found events missing from a CPU's ring: sequence
numbers it never read and never stored. KMES overwrote them before eventd
read them, or eventd consumed them while it had nowhere to store them.

`event.time` is the time of the ring event that revealed the gap, so
`loss.preceding-time` and `event.time` bound when the lost events were
written, and the record sorts beside that event. It is not when eventd
noticed, which after a restart can be much later. Where eventd consumed the
events itself while it had nowhere to store them, it is the time of the
last of them. The record also carries the ring's CPU as `event.cpu`.

Replaces `synthetic.gap` (PEI-617). Its `cpu_id` became `buffer.cpu`
(PEI-1390), and its `revealing_timestamp` the record's `event.time`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`buffer.cpu`](~peios/events/field-index/fields-buffer#buffer.cpu) | `uint` | required | The logical CPU whose ring buffer a record concerns. |
| [`loss.sequence`](~peios/events/field-index/fields-loss#loss.sequence) | `uint` | required | The first sequence number a loss covers. |
| [`loss.sequence-last`](~peios/events/field-index/fields-loss#loss.sequence-last) | `uint` | required | The last sequence number of a gap, where `loss.sequence` is the first. |
| [`loss.count`](~peios/events/field-index/fields-loss#loss.count) | `uint` | required | The number of events lost in one occurrence. |
| [`loss.preceding-time`](~peios/events/field-index/fields-loss#loss.preceding-time) | `uint.time` | optional | The time of the last record received before a gap, in nanoseconds since the Unix epoch. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

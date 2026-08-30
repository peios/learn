---
title: Gap Detection
description: Per-CPU sequence numbers are the whole mechanism — what causes a gap, what a gap record holds, and how lapping is detected.
---

Every event carries a per-CPU, per-boot sequence number, and a drain
thread knows what it last saw. That is the whole mechanism: an event
whose sequence number exceeds the expected next one means the numbers in
between belonged to events eventd never received.

During restart reconciliation, "expected" is the union of committed
receipt coverage and surviving ring records rather than one last-seen
number. A sequence already covered by either source is not a gap (§2.2).

## Causes

- **Ring buffer overrun.** KMES overwrote events before eventd read
  them. The most serious case: it means audit events were lost
  irrecoverably.
- **Structural drops.** KMES declined to write an event that exceeded
  its size limits.
- **Downtime.** Events emitted while eventd was not running.

All three appear identically at the consumer, which is why the record
says what was lost rather than why.

## Gap records

On detecting a jump, the drain thread generates a gap record carrying:

- the CPU identifier
- the first missing sequence number, the last seen plus one
- the last missing sequence number, the revealing event's minus one
- the count of missing events
- the timestamp of the last event successfully processed on this CPU,
  where one is known
- the timestamp of the event that revealed the gap

The record is written into the shard database through the normal write
path — handed to the same writer thread, batched with ordinary events,
committed in the same transaction. That transaction's receipt range
covers the missing sequence interval as well as any real event rows, so
a restart never emits the same gap twice (§3.1). It is not emitted
through KMES, which would be circular: the mechanism for recording that
the event transport lost something cannot depend on that transport.

The gap details are stored as a MessagePack map in the `payload` column
(§3.2), and gap records are queryable exactly like any other event.

## The CPU column

A gap record populates `cpu_id` and leaves the other KMES header columns
— `sequence`, `origin_class`, the identity GUIDs — null (§3.1).

`cpu_id` is populated deliberately, and it is the one place a synthetic
event carries a header field. Without it, `EVENTS WHERE cpu_id == 3`
would return every event from CPU 3 *except* the record saying that
events from CPU 3 went missing — which is the one record such a query
most needs to return.

`sequence` stays null because a gap record has no place in the sequence:
it describes numbers that were skipped, and giving it one of them would
make it indistinguishable from the event that was lost. It is also what
keeps gap records distinct from real events; `receipt_ranges` records
the accounted sequence interval separately (§3.1).

## Lapping

If `read_pos` falls behind `tail_pos`, the consumer has been lapped and
the PSPK read protocol advances it to `tail_pos`.

Lapping needs no special handling here. The next event read is the
oldest survivor, its sequence number is far beyond what the thread
expected, and ordinary gap detection records the difference. The
lapping case and the restart case produce the same record by the same
path.

---
title: Gap Detection
---

## Sequence gap detection

Each drain thread MUST track the last seen sequence number for its CPU. When an event is read from the ring buffer, the drain thread MUST compare the event's sequence number against the expected next sequence number (last seen + 1).

If the event's sequence number is greater than expected, the intervening sequence numbers represent lost events. Events may be lost due to:

- Ring buffer overrun (KMES overwrote events before eventd read them).
- Event drops (KMES dropped events due to structural size limits).
- Events lost during an eventd restart (events emitted while eventd was not running).

## Gap records

When a sequence gap is detected, the drain thread MUST generate a synthetic gap record containing:

- The CPU ID.
- The first missing sequence number (last seen + 1).
- The last missing sequence number (current event's sequence number - 1).
- The count of missing events (last missing - first missing + 1).
- The timestamp of the last successfully processed event on this CPU (if available).
- The timestamp of the event that revealed the gap.

The gap record is written directly to the shard database as part of the normal write path. It is not emitted through KMES. Gap records are stored alongside regular events and are queryable through the same interface.

## Lapping

If the drain thread's `read_pos` falls behind the ring buffer's `tail_pos` (the consumer has been lapped), the drain thread advances to `tail_pos` as specified by the PSD-003 read protocol. The sequence gap between the last processed event and the first event at `tail_pos` is detected and recorded as a gap record through the normal gap detection mechanism.

## Gap records in the event table

Gap records are stored in the `events` table with `event_type = 'synthetic.gap'`. The `cpu_id` column MUST be populated with the CPU ID on which the gap was detected. Other KMES header columns (`sequence`, `origin_class`, identity GUIDs) are NULL. The gap details (missing sequence range, surrounding timestamps) are stored as a msgpack map in the `payload` column. Gap records are queryable through the same interface as all other events. Populating `cpu_id` ensures that `EVENTS WHERE cpu_id == N` correctly returns gap records for CPU N.

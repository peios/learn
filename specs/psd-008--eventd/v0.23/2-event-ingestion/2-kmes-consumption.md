---
title: KMES Consumption
---

## Attachment

On startup, eventd MUST call `kmes_attach` (PSD-003 §4.1) to obtain one file descriptor per CPU. eventd MUST map each file descriptor to obtain the per-CPU ring buffer. The caller's effective token MUST hold SeSecurityPrivilege.

eventd MUST read the `capacity` value returned by `kmes_attach` and use it to compute the mapping size (`8192 + 2 * capacity`).

## Drain threads

eventd MUST create one drain thread per CPU. Each drain thread is responsible for reading events from exactly one per-CPU ring buffer. A drain thread MUST NOT read from more than one ring buffer.

Each drain thread MUST follow the read protocol defined in PSD-003 §5.1, including:

- Initialising `read_pos` to `tail_pos` on first attachment, starting from the oldest surviving event.
- Following the drain loop: load `write_pos` with acquire, check for lapping via `tail_pos`, validate event structural integrity, advance `read_pos` by `event_size`.
- Performing the torn read check (re-reading `tail_pos` after reading an event to detect concurrent overwrite).
- Using the notification wait protocol (`need_wake`, `futex_wait`) when no events are available, to avoid spinning.

## Event copying

When a drain thread reads an event from the ring buffer, it MUST copy the event data (header and payload) into process-local memory before advancing `read_pos`. The drain thread MUST NOT pass pointers into the mapped ring buffer region to the writer thread, as the ring buffer memory may be overwritten by KMES at any time after `read_pos` advances past the event.

The copy is bounded by the event's `event_size` field. The drain thread MUST NOT read beyond `event_size` bytes from the event's position in the ring buffer.

## Generation changes

After completing a drain cycle, the drain thread MUST check the ring buffer's `generation` field as specified in PSD-003 §5.1. If the generation has changed (due to a ring buffer resize triggered by a BufferCapacity configuration change), the drain thread MUST:

1. Record the sequence number of the last successfully processed event.
2. Call `kmes_attach` to obtain new file descriptors.
3. Map the new ring buffer for this CPU.
4. Scan events in the new buffer to find the first event with a sequence number greater than the recorded sequence number.
5. Resume draining from that position.

Events MUST NOT be lost or duplicated during a generation change.

## Sequence tracking

Each drain thread MUST maintain the last seen sequence number for its CPU. This value is used for gap detection (§2.3) and for resumption after generation changes or restarts.

On startup, if eventd has previously persisted data for this boot (identified by boot ID), it MUST read the last persisted sequence number per CPU from the event store and initialise the drain thread's sequence tracking from that value. This allows eventd to detect gaps that span a restart.

If no prior data exists for the current boot, the drain thread initialises its sequence tracker to 0 (no events seen). The first event on each CPU has sequence number 1 (PSD-003 §2.1).

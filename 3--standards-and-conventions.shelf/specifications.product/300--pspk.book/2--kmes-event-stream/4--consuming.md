---
title: Consumer Protocol
description: The consumer protocol — draining a ring, detecting loss, waiting for notification, handling buffer replacement, and the memory ordering it all rests on.
---

A consumer typically dedicates one thread to each buffer. Each thread
independently drains its buffer, sleeps when the buffer is empty, and
re-attaches when the buffer is replaced. The protocol uses no locks
and, while events are available, no system calls.

Each consumer keeps its own `read_pos` in its own memory. On first
attaching to a buffer, a consumer SHOULD set `read_pos` to the
buffer's current `tail_pos`, which starts it at the oldest surviving
event.

## Draining

1. Load `write_pos` with acquire ordering. If `write_pos == read_pos`,
   no events are available: go to the notification wait.
2. Load `tail_pos` with acquire ordering. If `read_pos < tail_pos`,
   the events at the read position have been overwritten and the
   consumer has been lapped: set `read_pos = tail_pos`. The skipped
   span is lost, and will show up as a sequence gap.
3. Save the current `tail_pos` as `saved_tail`.
4. Read the event at data region offset `read_pos & (capacity - 1)`.
5. Re-read `tail_pos`. If it has advanced past `saved_tail` and
   `read_pos < tail_pos`, the event was overwritten while it was being
   read. The bytes just read MUST be discarded: go to step 2.
6. Check that `event_size > 0` and `event_size >= header_size`. If
   either fails, the bytes are not a valid event; the consumer SHOULD
   set `read_pos = tail_pos` and go to step 2. A consumer MUST perform
   this check: an `event_size` of zero would otherwise make the drain
   loop spin forever.
7. Process the event. Advance `read_pos` by the event's `event_size`.
   Go to step 1.

A consumer MUST NOT read beyond an event's `event_size` boundary.

Steps 3 and 5 are what make a lock-free read safe against a producer
that is overwriting the region being read. A consumer that omits the
re-read can process a torn event assembled from two different events'
bytes.

## Detecting loss

A consumer SHOULD track the last sequence number it processed for each
CPU. A gap means events were lost, whether because they were
overwritten before being read or because the kernel dropped them
before they reached the buffer. The size of the gap is the number of
events lost.

Loss is a normal condition under load, not an error: the buffer
preserves recent events at the cost of old ones. A consumer SHOULD
report loss rather than treating it as fatal.

## Notification wait

When a buffer is empty:

1. Store 1 to `need_wake` with release ordering.
2. Re-load `write_pos` with acquire ordering. If events arrived
   between the drain loop finding the buffer empty and this store,
   clear `need_wake` to 0 and return to the drain loop. This re-check
   is REQUIRED: without it, an event written in that window would find
   `need_wake` still clear, and the consumer would sleep with events
   waiting.
3. Read `futex_counter`.
4. Optionally spin, re-checking `write_pos`. If events arrive during
   the spin, clear `need_wake` to 0 and return to the drain loop. The
   spin duration is the consumer's choice, and a consumer MAY omit
   this step entirely.
5. Call `futex_wait(&futex_counter, last_seen_value)`, where
   `last_seen_value` is the value read in step 3. The kernel puts the
   thread to sleep only if `futex_counter` still holds that value, so
   a wake that arrived in the meantime is not missed.
6. On waking, clear `need_wake` to 0 and return to the drain loop.

The futex address is the `futex_counter` field in the mapped producer
metadata page. This is a **shared** futex, keyed by the page's backing
inode, and a consumer MUST wait on it as such: a wait issued with
`FUTEX_PRIVATE_FLAG` will never be woken.

Clearing `need_wake` to 0 in steps 2, 4, and 6 MAY be a relaxed store.
If KMES reads a stale set value after the consumer has cleared it, it
performs a wake on a thread that is already awake, which is harmless.

Under sustained load a consumer never reaches the notification wait:
it stays in the drain loop, `need_wake` stays 0, and the producer's
notification cost is a single byte read per event.

## Buffer replacement

KMES replaces every buffer when its configured capacity changes.
Replacement preserves as many surviving events as the new capacity
allows and keeps sequence numbering continuous, but it invalidates
positions: the events are re-compacted from position 0 in the new
buffer, so the consumer's `read_pos` means nothing there.

After each drain cycle — the buffer emptied, or a batch limit reached
— a consumer SHOULD read `generation`. If it differs from the value
last seen:

1. Record the sequence number of the last event successfully processed
   from this buffer.
2. Finish draining the old buffer up to its `write_pos`, which is now
   frozen: KMES has stopped writing to it. A consumer MUST complete
   this drain before switching, or it loses every event written
   between its read position and the switchover.
3. Call `kmes_attach` for the same CPU to obtain a descriptor for the
   replacement buffer, and map it.
4. Read the new buffer's `capacity`, `write_pos`, and `tail_pos`.
5. Scan the new buffer for the first event whose sequence number is
   greater than the recorded one, and set `read_pos` to that event's
   position. A consumer MUST locate its position by sequence number
   and MUST NOT carry `read_pos` across.
6. Close the old descriptor and unmap the old buffer.
7. Resume draining from the new buffer.

The old buffer's pages remain valid for as long as any consumer keeps
them mapped, so a consumer is never racing to finish before the memory
disappears.

If the new capacity is large enough to hold everything that survived
in the old buffer, no events are lost across the replacement. If it is
smaller, the oldest surviving events are discarded until the remainder
fits — the same overwrite semantics applied against the smaller
capacity — so loss is bounded to the oldest part of the buffer and
appears as a sequence gap.

A consumer sleeping on the old buffer is woken when the replacement
happens, provided its `need_wake` was set, so it observes the
generation change rather than sleeping indefinitely on a buffer that
will never receive another event.

## Memory ordering

| Operation | Ordering | Purpose |
|---|---|---|
| Producer stores `tail_pos` | release | The advanced tail is visible before the data that replaces the events it skipped past. |
| Producer stores `write_pos` | release | Complete event data is visible before the position that makes it reachable. |
| Producer stores `futex_counter` | release | A consumer waking from the futex observes all prior writes. |
| Consumer stores `need_wake = 1` | release | The producer observes the flag before the consumer waits. |
| Consumer stores `need_wake = 0` | relaxed | A stale read causes only a spurious wake. |
| Consumer loads `write_pos` in the drain loop | acquire | Pairs with the producer's release. |
| Consumer loads `write_pos` after setting `need_wake` | acquire | Closes the window between finding the buffer empty and announcing the sleep. |
| Consumer loads `tail_pos` | acquire | Pairs with the producer's release. |

For a given buffer there are exactly two kinds of party: one producer,
which is the kernel on the owning CPU, and any number of consumers.
There is no multi-producer contention to account for.

On x86-64 the producer's release stores compile to plain stores,
because the architecture does not reorder stores with other stores.
Consumers MUST NOT rely on that: the ordering above is required for
correctness on weaker architectures, and a consumer written without it
is incorrect on those machines whether or not it is observed to fail
on x86-64.

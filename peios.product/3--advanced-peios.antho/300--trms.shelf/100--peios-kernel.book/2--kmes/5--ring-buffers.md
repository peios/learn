---
title: Ring Buffers
description: One ring per logical CPU — how they are organised, the two producer metadata pages, wrap handling, the write protocol and notification.
---

## Organisation

KMES maintains one ring buffer per logical CPU, created for every CPU
in the kernel's possible-CPU set when the module initialises — before
LCS exists, using the compiled-in default capacity — and buffering
events from that first instant. These boot-time buffers are ordinary
buffers: same layout, same overwrite semantics, same generation
model, immediately attachable. If LCS never becomes available they
simply remain the live buffers indefinitely. [*ring.created-at-init-for-possible-cpus]

Each ring is an independent, reference-counted object holding its
capacity, generation, sequence counter, write and tail positions,
futex counter, dropped-event counter, two metadata pages, and the data
region. There is no shared state between rings on the write path: each
CPU writes only to its own ring, using plain non-atomic fields under
preemption disablement, and the only ordering machinery is a set of
release stores at publication points. Fds taken by consumers hold
references, so a ring — including a superseded generation — survives
until the last consumer releases it. [*ring.independent-refcounted]

The data region is a `vzalloc` allocation of exactly `capacity` bytes,
zeroed once at creation and never scrubbed afterwards; overwritten
regions retain stale bytes, which is why the consumer contract forbids
reading beyond an event's `event_size`. [*ring.data-zeroed-once-not-scrubbed] Capacity is always a power of
two — enforced at every entry point — so position wrap is a bitwise
AND with `capacity - 1`. The permitted range is 64 KB to 256 MB, with
a 4 MB default. [*ring.capacity-range]

## The two producer metadata pages [*ring.mirrored-metadata-stores]

Producer metadata exists twice. The kernel writes its working copy to
a private page allocated with the ring, and mirrors every store to a
second, consumer-visible page. The consumer-visible page is
shmem-backed and allocated lazily at the first `kmes_attach` for the
ring; shmem backing is what makes the notification futex work, since
a shared (inode-keyed) futex needs a page-backed mapping. [*ring.shared-page-lazy-shmem] Every
producer store — `write_pos`, `tail_pos`, `futex_counter`,
`generation` — is a release store performed to both pages; the static
fields are initialised at ring creation and re-stamped when the shared
page appears. The mmap handler exposes only the shared page. The field
offsets on the page are part of the consumer contract, defined in the
PSPK event stream chapter.

## Wrap handling [*ring.consumer-sees-contiguous-wrap]

The consumer's data region is double virtual mapped — the same
physical pages appear twice consecutively — so a consumer reads an
event that crosses the physical end of the buffer as one contiguous
byte sequence. The producer side has no such mapping: kernel writes
into the `vzalloc` region are wrap-aware, splitting a byte-range copy
that crosses the boundary into two `memcpy` calls and masking scalar
stores per byte. The contiguity guarantee is a property of the
consumer's view, produced by the mmap layout rather than by the
writer.

## Write protocol [*ring.lock-free-single-writer]

Each ring has exactly one writer — its CPU — and the write path takes
no locks and performs no cross-CPU atomics. For a single kernel
emission: capture the timestamp; take the next sequence number; if
the event fails a structural check, count the drop and stop (§2.3);
otherwise make room, write the event at `write_pos & (capacity - 1)`,
publish the new `write_pos` (old value plus event size) with a
release store, and check `need_wake`. The release store is what makes
the event atomic from the consumer's side: the bytes are complete
before the position that makes them reachable moves.

Making room is the overwrite walk. While the live span
(`write_pos - tail_pos`) plus the incoming event exceeds capacity,
KMES reads the `event_size` of the event at the tail and advances
`tail_pos` past it, counting each overwritten event in the internal
dropped-event counter, and publishes the advanced tail with a release
store before the new data lands on top of it. [*ring.overwrite-advances-tail-first] Walking the tail is
sequential and possibly cache-cold — the tail can be megabytes from
the write position — a cost accepted in preference to maintaining an
index of event offsets on the hot write path.

The walk carries a corruption guard: if the size field read at the
tail is zero, larger than the capacity, or larger than the live span,
KMES abandons the walk and resynchronises by jumping `tail_pos`
straight to `write_pos`, discarding the entire surviving window in
one step (the discarded span is not itemised in the drop counter) and
emitting a tracepoint. [*ring.tail-resync-guard]

During batch writes the running write and tail positions are kept in
locals; nothing is published until the batch ends, when the tail and
then the write position get one release store each, followed by a
single `need_wake` check — provided at least one event was written.
Consumers therefore observe a batch atomically, and see one tail
transition per batch rather than one per overwritten event. [*ring.batch-one-tail-transition]

## Notification [*ring.need-wake-protocol]

The wake path reads the consumer page's `need_wake` byte — the single
consumer-writable byte KMES ever reads, treated as a boolean and
trusted for nothing else. If it is zero, notification costs that one
read. If set, KMES increments the futex counter with a release store
and wakes every thread waiting on it. The futex is a shared,
inode-keyed futex on the shmem producer page at the counter's offset —
a consequence a consumer must match: a `FUTEX_PRIVATE_FLAG` wait on
the mapped address is never woken. [*ring.futex-is-shared-inode-keyed] Before any consumer has attached,
the shared page does not exist and the wake is skipped entirely,
though the private counter still advances. [*ring.wake-skipped-before-attach]

The `futex_wake` call itself is issued after preemption is re-enabled,
outside the write window; only the counter increment happens inside
it. Waking a thread that is already awake is a harmless no-op, which
is also why the consumer's relaxed clearing of `need_wake` is safe.

## Capacity swaps [*ring.swap-under-stop-machine]

A valid `BufferCapacity` configuration change replaces every ring.
New rings are allocated first, at the old generation plus one, fully
initialised before any CPU can see them. The switch itself runs under
`stop_machine`: with every CPU quiesced, each ring's surviving events
are migrated to its replacement, the per-CPU live pointers are
switched, and each old ring's published generation is bumped to the
new value — signalling consumers on the old mapping to re-attach. [*ring.swap.generation-bump-signals-reattach] If
an old ring's `need_wake` is set, its futex counter is bumped inside
the quiesced section and the wake is issued after it, so consumers
asleep on a dead generation do not sleep forever. [*ring.swap.wakes-stale-sleepers]

Migration copies the surviving span in sequence order, re-compacted
contiguously from position zero: the new ring starts with
`tail_pos = 0` and `write_pos` equal to the bytes copied, and the
sequence and dropped-event counters carry over, so sequence numbers
are continuous across a swap. [*ring.swap.migration-recompacts] When the new capacity is smaller than
the surviving span, the oldest events are skipped from the tail
forward until the suffix fits — loss is bounded to the oldest prefix,
traced but not counted as drops. [*ring.swap.shrink-skips-oldest] Old positions are meaningless in the
new ring; a consumer re-locates by sequence number, per the PSPK
protocol.

If allocating the new rings fails, the old rings stay live at their
size, no generation changes, and the failure is reported through a
`KMES_BUFFER_SWAP_FAILED` event (§2.6). [*ring.swap.alloc-failure-keeps-old] A migration abort — a corrupt
size field encountered inside the quiesced section — abandons the
swap the same way but emits no event. [*ring.swap.abort-emits-no-event] There is no automatic retry;
the next configuration write or reboot tries again. A superseded
generation's pages stay valid for as long as any consumer keeps them
mapped, so during and after a swap old and new rings coexist until
the last old fd closes. [*ring.swap.generations-coexist]

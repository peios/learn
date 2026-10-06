---
title: "buffer.*"
description: "Every field the evman catalogue defines under buffer: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `buffer`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="buffer.capacity"></a>`buffer.capacity`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The per-CPU ring buffer capacity in force. After a failed swap, the
capacity that was kept.

**Carried by:**

- [`kmes.buffer.swap.failed`](~peios/events/kmes/kmes-buffer-swap-failed)

## <a id="buffer.capacity-expected"></a>`buffer.capacity-expected`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The ring capacity a record expected to find, where the ring it found has
another. Every per-CPU ring is meant to share one capacity, because KMES
sizes an incoming event against one ring's capacity before writing it to
another. A ring whose `buffer.capacity` differs from this has broken that
check: an event judged to fit may not fit the ring it lands in.

**Carried by:**

No event carries this field yet.

## <a id="buffer.capacity-previous"></a>`buffer.capacity-previous`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The per-CPU ring capacity before a capacity swap: what `buffer.capacity`
was until the swap committed. A swap to a smaller capacity copies the
surviving events into the new rings and skips any that no longer fit, so a
record where this exceeds `buffer.capacity` is one where the swap itself
can have lost events.

**Carried by:**

No event carries this field yet.

## <a id="buffer.capacity-requested"></a>`buffer.capacity-requested`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The per-CPU ring buffer capacity that was asked for.

**Carried by:**

- [`kmes.buffer.swap.failed`](~peios/events/kmes/kmes-buffer-swap-failed)

## <a id="buffer.cpu"></a>`buffer.cpu`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The logical CPU whose ring buffer a record concerns. KMES keeps one ring
per CPU and writes each event to the ring of the CPU it was emitted on, so
this is the numbering `event.cpu` uses on records read from that ring. It
identifies a ring, not a security subject, and it is the only thing that
does.

**Carried by:**

No event carries this field yet.

## <a id="buffer.cpu-claimed"></a>`buffer.cpu-claimed`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The CPU a ring's own metadata says it belongs to, carried when that
disagrees with `buffer.cpu`, the CPU it is installed for. A disagreement
means the ring topology is internally inconsistent, and KMES drops the
event rather than trust the ring. **It consumes no sequence number and
counts no loss**, so no gap appears in `event.sequence`, and a record
carrying this field is the only evidence that the event existed.

**Carried by:**

No event carries this field yet.

## <a id="buffer.fill"></a>`buffer.fill`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

How full a ring was, as the bytes of events it held: `buffer.head` minus
`buffer.tail`. Compare it with `buffer.capacity` for a proportion. A full
ring loses its oldest events to every new one, so a fill near capacity is
the warning that comes before loss rather than loss itself.

**Carried by:**

No event carries this field yet.

## <a id="buffer.generation"></a>`buffer.generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The generation of the ring in force. It starts at 1 and goes up by one
with each capacity swap, which replaces every ring with a new one. The old
ring is stamped with the new generation as it is retired, so a consumer
still mapping it can tell that its view is stale; it is the only
staleness signal a mapped ring has.

**Carried by:**

No event carries this field yet.

## <a id="buffer.generation-previous"></a>`buffer.generation-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The ring generation before a capacity swap, normally one less than
`buffer.generation`.

**Carried by:**

No event carries this field yet.

## <a id="buffer.head"></a>`buffer.head`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The ring's write position, as a running byte count. It only increases and
never wraps: it is not an offset into the buffer, which is this value
modulo `buffer.capacity`. With `buffer.tail` it gives the ring's fill
directly.

**Carried by:**

No event carries this field yet.

## <a id="buffer.slots"></a>`buffer.slots`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of per-CPU ring slots the kernel exposes: one for every CPU
the system could have, numbered as `buffer.cpu` is. A consumer that means
to see every event attaches to every slot. A slot for a CPU that is not
present holds no ring.

**Carried by:**

No event carries this field yet.

## <a id="buffer.tail"></a>`buffer.tail`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The ring's tail position: where its oldest retained event begins, as a
running byte count in the same terms as `buffer.head`. It moves forward
when the ring is full and new events overwrite the oldest, so a tail that
has passed the point a consumer was reading from means that consumer lost
events.

**Carried by:**

No event carries this field yet.

## <a id="buffer.threshold-direction"></a>`buffer.threshold-direction`

- **Type:** `str.enum`
- **Values:** `rising` · `falling`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

Whether a ring's fill crossed a watermark on the way up or on the way
down. `rising` is the warning that a consumer is falling behind; `falling`
is its recovery. Without it, a record of recovery cannot be told from a
record of onset.

**Carried by:**

No event carries this field yet.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

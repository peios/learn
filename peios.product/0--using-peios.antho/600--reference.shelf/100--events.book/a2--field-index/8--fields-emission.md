---
title: "emission.*"
description: "Every field the evman catalogue defines under emission: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `emission`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="emission.batch-index"></a>`emission.batch-index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The zero-based position, in a batch emit, of the entry that failed. **A
batch is emitted up to this entry and not from it**: every earlier entry
reached the ring, and this entry and every later one did not.

**Carried by:**

No event carries this field yet.

## <a id="emission.buckets-clamped"></a>`emission.buckets-clamped`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of per-process rate buckets a reconfiguration cut down.
Lowering `emission.rate-limit` clamps the remaining budget of every live
process to the new ceiling at once; this counts the processes whose budget
was above it.

**Carried by:**

No event carries this field yet.

## <a id="emission.budget"></a>`emission.budget`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of events a process could still emit before its rate limit
stopped it: the tokens left in its bucket when the record was made. The
bucket refills at `emission.rate-limit` events a second and holds no more
than that, so a process's burst is one second's worth. On a throttled
emit this is below `emission.requested`, which is why the emit was
refused.

**Carried by:**

No event carries this field yet.

## <a id="emission.emitted"></a>`emission.emitted`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of events an emit operation actually wrote to the ring. Where
it falls short of `emission.requested`, the difference is events the
caller meant to record that are not in the stream.

**Carried by:**

No event carries this field yet.

## <a id="emission.length"></a>`emission.length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The total size of one event as written to the ring: the fixed header, the
event type and the payload together. It is the figure checked against the
configured maximum event size, and against half the ring's capacity, the
largest event a ring accepts.

**Carried by:**

No event carries this field yet.

## <a id="emission.length-claimed"></a>`emission.length-claimed`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

An event length read from a ring that failed KMES's sanity check: zero,
larger than the ring, or larger than the bytes between the tail and the
write position. It is not the size of any real event. It means the ring's
framing is corrupt, and KMES recovered by discarding everything pending in
that ring at once — a loss that is never added to the ring's dropped
count and is bounded only by the ring's size.

**Carried by:**

No event carries this field yet.

## <a id="emission.payload-length"></a>`emission.payload-length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The byte length of an event's MessagePack payload, without the header or
the event type.

**Carried by:**

- [`peinit.event.dropped`](~peios/events/peinit/peinit-event-dropped)

## <a id="emission.rate-limit"></a>`emission.rate-limit`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The per-process emission ceiling KMES is running on, in events a second:
the `MaxEmitRatePerProcess` registry value, 10 000 by default and accepted
from 100 to 1 000 000. It applies to emission from userspace; kernel
emitters are not limited, and a process holding SeTcbPrivilege is exempt.

**Carried by:**

- [`kmes.config.applied`](~peios/events/kmes/kmes-config-applied)

## <a id="emission.rate-limit-previous"></a>`emission.rate-limit-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The per-process emission ceiling before a reconfiguration, in events a
second. Lowering the ceiling is a way to thin out the event stream, so a
record where this exceeds `emission.rate-limit` deserves a look at who
changed it.

**Carried by:**

No event carries this field yet.

## <a id="emission.requested"></a>`emission.requested`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The number of events an emit operation asked to write: 1 for a single
emit, or the entry count of a batch, which is at most 256.

**Carried by:**

No event carries this field yet.

## <a id="emission.throttled"></a>`emission.throttled`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

How long a producer was held back by its rate limit, from the first emit
refused for want of budget to the first accepted again. A duration, not a
flag. Every emit refused in that span was an event the producer meant to
record that is not in the stream.

**Carried by:**

No event carries this field yet.

## <a id="emission.type"></a>`emission.type`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The event type an emitter was trying to emit, as it supplied it. It names
what was attempted, not what was recorded: a record carrying it is about
an emission that failed or was cut short, and no event of this type need
exist. Absent where the type itself was the fault — empty, or not valid
UTF-8 — in which case `emission.type-length` still gives its length.

**Carried by:**

- [`peinit.event.dropped`](~peios/events/peinit/peinit-event-dropped)

## <a id="emission.type-length"></a>`emission.type-length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kmes.evman`

The byte length of the event type an emitter supplied, at most 65 535.

**Carried by:**

No event carries this field yet.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

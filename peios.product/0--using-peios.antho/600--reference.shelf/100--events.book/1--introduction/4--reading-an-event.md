---
title: Reading an Event
description: The rules every consumer of this stream lives by — ignore unknown keys, read absence against a field's declared presence, expect loss, and do not trust the contents.
---

Four rules govern every consumer of this stream.

## Ignore unknown keys

Future versions may add fields to an event without changing the existing
ones. A consumer that processes the keys it knows and ignores the rest
keeps working across upgrades. A consumer that rejects unrecognised keys
breaks on the first addition.

## Read absence by the field's presence

A key that is absent means the emitter had no value for it (§1.3) —
nothing more. Each event page says when each field is present:
`required`, `optional`, or `when` a condition on another field holds.
Read absence against that, not as a signal of its own. A field that is
optional today may become always present later.

## Delivery is best-effort

KMES is a ring buffer. The kernel writes; keeping up is the subscriber's
problem.

- A subscriber that falls behind **loses events**. eventd notices and
  records an [`eventd.events.lost`](~peios/events/eventd/eventd-events-lost),
  which is how a gap becomes visible
  rather than silent.
- **There is no replay.** An event missed is gone. Nothing can ask for
  it back.
- **Buffers are per-subscriber.** One slow reader does not affect
  another.
- **Order is per-subscriber**, not global.

For durable audit, read events from eventd's stores rather than from
KMES directly. eventd drains its subscription continuously and persists
what it reads; from that point the store is the record, not the ring.

## Events are not authenticated

Events are trusted because they came through KMES, not because they are
signed. Nothing in an event carries a signature. What the kernel vouches
for is the header: `emitter.class` says which path wrote a record, and a
program can write any event type it likes with class `0` (§1.2).

Cryptographic non-repudiation is a userspace concern applied after
events leave the kernel. If a deployment needs it, it is added on the
far side of eventd, not here.

## Versioning

Event types are not versioned by a field. Some changes to the catalogue
are additive and can arrive in any update: a new event type, a new
field, a new value of an open enumeration. A consumer that ignores what
it does not know, and treats an unknown value of an open enumeration as
a value, keeps working across them.

Renaming an event type or a field, moving a field to another path,
changing a field's type, or adding a value to a closed enumeration is
not additive. Each needs a new version of the event vocabulary, because
every query and descriptor written against the old shape stops matching
(PGSS §6.11).

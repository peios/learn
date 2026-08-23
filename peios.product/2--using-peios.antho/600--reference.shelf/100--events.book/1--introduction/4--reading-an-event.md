---
title: Reading an Event
description: The four rules every consumer of this stream lives by — ignore unknown keys, do not read meaning into absence, expect loss, and do not trust the contents.
---

Four rules govern every consumer of this stream.

## Ignore unknown keys

Future versions may add fields to an event without changing the existing
ones. A consumer that processes the keys it knows and ignores the rest
keeps working across upgrades. A consumer that rejects unrecognised keys
breaks on the first addition.

## Do not rely on a key being absent

A field that is optional today may become always-present later. Absence
is not a signal.

## Delivery is best-effort

KMES is a ring buffer. The kernel writes; keeping up is the subscriber's
problem.

- A subscriber that falls behind **loses events**. eventd notices and
  records a `synthetic.gap` (§8.1), which is how a gap becomes visible
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

Events are trusted because they came from the kernel through KMES, not
because they are signed. Nothing in an event carries a signature.

Cryptographic non-repudiation is a userspace concern applied after
events leave the kernel. If a deployment needs it, it is added on the
far side of eventd, not here.

## Versioning

Event types are not versioned by a field. The schemas in this book are
stable: fields may be added, but an existing field will not be renamed,
retyped or removed under the same type string.

A change that would break compatibility changes the **type string**
instead — `access-audit` would become `access-audit-v2` — so an existing
consumer keeps receiving the shape it understands and simply never sees
the new one. No type in this book has been versioned that way.

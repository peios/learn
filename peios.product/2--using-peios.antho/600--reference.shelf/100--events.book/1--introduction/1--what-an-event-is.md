---
title: What an Event Is
description: What counts as an event on a Peios system, where this book's schemas come from, the two transports that carry events, and what this book deliberately leaves out.
---

An **event** is a record that something happened: an access was checked,
a service started, a package was installed, a descriptor was found
corrupt. Events are produced by the component that observed the thing,
and consumed by whatever is watching — usually `eventd`, sometimes a
tool reading the stream directly.

This book enumerates every event Peios emits, with the fields each one
carries. It is a lookup, not an explanation. Where an event's *meaning*
needs the mechanism behind it, the page links to the manual that
describes that mechanism.

## Where the schemas come from

Every event type and every field is defined in the **evman catalogue**:
the `.evman` fragments each component installs in `/usr/share/evman/`
(PGSS §6.10). The catalogue is the definition, and most of this book is
generated from it:

- **§2** describes the **groups**, the sets of fields that travel
  together, such as `subject`.
- **§3 to §15** have a page per event type, one chapter per root: the
  kernel's `kacs`, `stratafs`, `lcs`, `kmes` and `ntfe` (§3 to §7), then
  `peinit`, `peipkg`, `eventd`, `authd`, `lpsd`, `timed`, `netd` and
  `trustd` (§8 to §15).
- **Appendix A** lists every event type in one table, and **Appendix B**
  is the field index: every field, its type and values, and every event
  that carries it.

On a running system, `evman <event-type>` prints the same definition
from the installed fragments ([evman](~peios/event-tools/evman)).

## Two transports, not one

Most events travel through **KMES**, the kernel message event stream: a
per-CPU ring buffer that the kernel writes into and userspace reads
from. Every KMES event is a binary header followed by a MessagePack
payload (§1.2).

Two things in this book never travel through KMES:

- **eventd's records about itself** (§10) are catalogue events, but
  eventd writes them straight into its event store and they never touch
  KMES. They carry no sequence number and no `emitter.*` stamps.
- **LCS watch records** (§16) are not events at all, and are included
  because an operator looking for "what does Peios tell me" would
  otherwise miss them. They are binary records read from a key file
  descriptor: a notification mechanism, not an audit trail, with a
  format that has nothing in common with a KMES event.

## What is not here

This book does not cover **logs** or **metrics**. Both reach eventd by a
different path, are stored in different tables, and are not events. The
eventd manual covers them.

Nor does it cover the query language for reading events back. That is
PSPU §3, with the operator-facing view in the eventd manual.

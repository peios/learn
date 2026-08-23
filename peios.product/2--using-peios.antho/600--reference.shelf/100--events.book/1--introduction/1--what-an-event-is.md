---
title: What an Event Is
description: What counts as an event on a Peios system, the two transports that carry them, and what this book deliberately leaves out.
---

An **event** is a record that something happened: an access was checked,
a service started, a package was installed, a descriptor was found
corrupt. Events are produced by the component that observed the thing,
and consumed by whatever is watching — usually `eventd`, sometimes a
tool reading the stream directly.

This book enumerates every event Peios emits, with the fields each one
carries. It is a lookup, not an explanation. Where an event's *meaning*
needs the mechanism behind it, the chapter links to the manual that
describes that mechanism.

## Two transports, not one

Most events travel through **KMES**, the kernel message event stream: a
per-CPU ring buffer that the kernel writes into and userspace reads
from. Every KMES event is a binary header followed by a msgpack
payload. Chapters 3 to 7 document KMES events.

Two things in this book are not KMES events, and are included because an
operator looking for "what does Peios tell me" would otherwise miss
them:

- **eventd's synthetic events** (§8) are written straight into a shard
  database and never touch KMES. They carry no header stamps.
- **LCS watch records** (§5.4) are binary records read from a key file
  descriptor. They are a notification mechanism, not an audit trail, and
  their format has nothing in common with a KMES event.

## What is not here

This book does not cover **logs** or **metrics**. Both reach eventd by a
different path, are stored in different tables, and are not events. The
eventd manual covers them.

Nor does it cover the query language for reading events back. That is
PSPU §3, with the operator-facing view in the eventd manual.

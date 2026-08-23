---
title: Overview
description: KMES is the sole event emission path in Peios, used by kernel subsystems and userspace alike, and the terms this chapter uses for it.
---

The Kernel Mediated Event Subsystem is the sole event emission path in
Peios. Kernel subsystems and userspace processes alike emit events
exclusively through KMES — there is no alternative path. KMES stamps
each event with trusted metadata at emission time, buffers it in
per-CPU shared memory ring buffers, and delivers it to userspace
consumers that map those buffers directly. It does not persist, index,
or query events, and it imposes no schema or naming convention on them;
those are consumer concerns, handled by eventd.

KMES serves a similar role to ETW in the Windows kernel and auditd in
Linux, but is compatible with neither at the wire, format, or API
level. The design — structured events with a fixed binary header and a
msgpack payload, shared memory delivery, one emission path for kernel
and userspace — was chosen for unified observability with
kernel-trusted metadata.

The consumer-facing contract — the event header layout, the mapped
ring buffer regions, and the protocols a consumer follows to drain,
sleep, and survive buffer swaps — is specified in PSPK's KMES event
stream chapter. This chapter describes the kernel side: how events are
constructed and stamped (§2.2), the in-kernel emission API (§2.3), the
syscall surface (§2.4), how the ring buffers are organised and written
(§2.5), self-configuration through the registry (§2.6), and behaviour
under failure (§2.7).

## Terminology

An **event** is an indivisible record: a packed binary **header**
carrying KMES-intrinsic metadata, followed by a msgpack-encoded
**payload** whose structure is defined by the emitter. Header and
payload are produced, stored, and consumed together as one contiguous
byte sequence; neither is meaningful alone. KMES treats the payload as
opaque.

The **stamp** fields are the header fields KMES populates itself at
emission time: the timestamp, sequence number, CPU identifier, and
origin class, plus three identity GUIDs captured from KACS — the
**effective token GUID** (the token governing the emitting thread's
access rights, which is the impersonation token when the thread is
impersonating), the **true token GUID** (the process's primary token,
regardless of impersonation), and the **process GUID** (assigned by
KACS at fork and unchanged across exec). The **null GUID** — sixteen
zero bytes — stamps an identity field whose value is unavailable.

The **sequence number** is a per-CPU, per-boot monotonic 64-bit
counter. Each CPU counts independently; the counter starts at zero
when PKM loads and is incremented before its value is taken, so the
first event on each CPU carries sequence number 1 and sequence 0 is
never assigned. A gap in one CPU's sequence indicates lost events. The
pair (`cpu_id`, `sequence`) uniquely identifies an event within a
boot; there is no global sequence.

The **origin class** is a header byte identifying the emission path:
userspace (0), KMES itself (1), KACS (2), or LCS (3). Values 4–255 are
unassigned.

The **event type** is a length-prefixed UTF-8 string in the header
identifying the kind of event. KMES imposes no structure on it and
compares nothing against it; types are consumer vocabulary.

A **ring buffer** is a per-CPU shared memory region — producer
metadata page, consumer metadata page, and a data region — created
and managed by KMES and mapped by consumers. A **consumer** is a
userspace process that maps one or more ring buffers and drains events
from them, typically with one thread per CPU. **Boot-time ring
buffers** are the ordinary per-CPU buffers created at module load
using compiled-in defaults; they are the live consumer-facing buffers
from the first instant, not a separate class.

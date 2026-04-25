---
title: Terminology
---

The following terms are used throughout this specification with the precise meanings defined here.

**PKM** (Peios Kernel Module): The single loadable kernel module (`pkm.ko`) containing all Peios kernel extensions. KMES, KACS, and LCS are peer subsystems within PKM.

**KMES** (Kernel Mediated Event Subsystem): The event subsystem within PKM. Provides the sole event emission path in Peios -- kernel subsystems and userspace processes emit events exclusively through KMES. KMES buffers events, stamps them with metadata, assigns per-CPU sequence numbers, and delivers them to userspace consumers via per-CPU shared memory ring buffers.

**Event**: An indivisible record consisting of a header and a payload. The header is a packed binary structure containing KMES-intrinsic metadata. The payload is a msgpack-encoded blob of arbitrary structured data defined by the emitter. Header and payload are always produced and consumed together -- neither is meaningful alone.

**Header**: The packed binary prefix of every event. Contains: event size, header size, wall clock timestamp, per-CPU sequence number, CPU identifier, origin class, and a length-prefixed event type string. The header also reserves space for future process and identity stamp fields.

**Payload**: The msgpack-encoded body of an event. Its structure is defined by the emitting subsystem or process. KMES treats the payload as opaque -- it buffers and delivers payloads without interpreting them.

**Stamp**: The set of metadata fields in the event header that KMES populates at emission time. v0.20 stamp fields are KMES-intrinsic: timestamp, sequence number, cpu_id, and origin class. Future versions will add process and identity fields in coordination with PSD-004.

**Sequence number**: A per-CPU, monotonically increasing 64-bit unsigned integer assigned by KMES to each event at emission time. Each CPU maintains its own independent counter, reset to zero when the PKM module loads. The counter is incremented before the value is taken, so the first event on each CPU receives sequence number 1. Sequence 0 is never assigned to an event. Gaps in the sequence on a given CPU indicate lost events (overwritten or dropped). The sequence number is not a global ordering primitive -- events are ordered primarily by timestamp.

**Origin class**: A header field identifying the subsystem or emission path that produced the event: a specific kernel subsystem (KMES, KACS, LCS) or userspace (via syscall).

**Event type**: An arbitrary, length-prefixed UTF-8 string in the event header identifying the kind of event. KMES imposes no structure or naming convention on event types -- schema and naming are consumer concerns.

**Ring buffer**: A per-CPU shared memory region created and managed by KMES, mapped into the address space of authorized userspace consumers. Each buffer consists of a producer metadata page (mapped read-only), a consumer metadata page (mapped read-write for consumer notification state), and a data region (mapped read-only, double virtual mapped). KMES maintains one ring buffer per CPU. Each buffer is independent, with its own write position, sequence counter, and futex notification. Ring buffers are the sole delivery mechanism from KMES to userspace.

**Boot buffer**: Internal per-CPU kernel buffers used by KMES to capture events during early boot, before the registry is available and the consumer-facing ring buffers are created. One boot buffer exists per CPU. Boot buffers are not visible to consumers. When the ring buffers are created, surviving boot buffer events are copied into them.

**Consumer**: A userspace process that maps one or more KMES ring buffers and reads events from them. Consumers typically dedicate one thread per CPU buffer. eventd is the primary consumer.

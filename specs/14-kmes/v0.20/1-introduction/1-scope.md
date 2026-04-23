---
title: Scope
---

This specification defines the Kernel Mediated Event Subsystem (KMES) for the Peios operating system. KMES is the event subsystem within the Peios Kernel Module (PKM), peer to KACS and LCS. It provides a unified event emission, buffering, and delivery mechanism for the Peios kernel.

KMES is the sole event emission path in Peios. All events -- whether originating from kernel subsystems or userspace processes -- are emitted through KMES. There is no alternative event path.

This specification covers:

- The event model -- event structure, header format, msgpack payload, and the header/payload boundary
- The emission API -- the internal kernel interface used by KACS and LCS to emit events
- The syscall interface -- the mechanism for userspace event emission and consumer attachment
- Event buffering and ordering -- per-CPU ring buffers, per-CPU sequence numbering, and wall clock timestamps
- The delivery mechanism -- per-CPU shared memory ring buffers, double virtual mapping, lock-free read/write protocols, and futex-based consumer notification
- Stamping -- KMES-intrinsic stamp fields (timestamp, sequence number, cpu_id, origin class); process and identity stamp fields are reserved for a future version pending KACS coordination

This specification does not cover:

- Event persistence, indexing, or querying (eventd)
- Event type schemas or naming conventions (eventd)
- Boot identity and cross-boot sequencing (peinit / eventd)
- KACS (covered by the KACS v0.20 specification)
- LCS (covered by the LCS v0.21 specification)
- Authentication or principal management (authd)

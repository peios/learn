---
title: Scope and Roles
description: What PGSS Events specifies and who its parties are — the emitter that writes an event and the consumer that reads it — and where the transport, storage and per-event reference are covered instead.
---

This chapter specifies **PGSS Events**: what an event on a Peios system
is called, what its payload carries and how, when it is written at all,
and how the vocabulary is catalogued.

The chapter rests on one decision. **A name is policy.** Every dot in an
event type is a place an administrator can attach a security descriptor,
and every field in a payload is an object an access check can grant or
deny. Two spellings of one value are two objects, and a descriptor that
denies one does not deny the other. So the names in this chapter are
fixed with the same care as an access mask, and each value has exactly
one of them.

Two roles participate.

| Role | Obligation |
|---|---|
| Emitter | Writes events. Everything an event is named, carries and encodes is an emitter obligation, as is deciding whether to write it at all (§6.9) and describing it in a fragment (§6.10). |
| Consumer | Reads events, or the catalogue that describes them. A store, a viewer, a forwarder and a policy editor are all consumers. Every rule about interpreting a name or a value binds the consumer. |

A kernel subsystem is an emitter, and so is a daemon, a service and an
application. The emitter role does not depend on the path an event takes
to the stream: an event a daemon writes through the emission system
calls and an event the kernel writes on a daemon's behalf (§6.7) are
both held to this chapter.

Both roles are publicly implementable. A third party MAY ship an emitter
or a consumer and interoperate with the rest unchanged. That is the
reason the vocabulary is specified rather than left to each component:
a consumer that searches for a principal searches every emitter's events
with one query, and an emitter that names its fields as specified is
found by every consumer without either knowing the other.

This chapter covers:

- the form of an event type, and who may use which root (§6.3)
- the form of a field path, the roles and domains a path leads with, and
  the names under which a consumer exposes the record header (§6.4)
- the encoding of every kind of value (§6.5)
- how an event records success and failure (§6.6)
- how access decisions are recorded, including those a userspace
  component makes about objects it guards (§6.7)
- what is an event rather than a log line or a metric, and the tier each
  event declares (§6.8)
- the emission policy that decides whether an event type is written at
  all (§6.9)
- the catalogue of event and field definitions, and the rules a
  definition must pass (§6.10)

This chapter does not cover:

- The record format, the header layout and the ring-buffer protocol a
  consumer follows to drain events. These are PSPK §2.
- How a process or kernel subsystem writes an event to the stream. The
  emission interfaces are described in the Peios Kernel TRM, and the
  libraries that wrap them in the SDK documentation.
- Storing, retaining and querying events, and per-field read access.
  The query language is PSPU §3; one implementation's storage and
  retention are described in the eventd TRM.
- The meaning of each event and field. That is reference material,
  generated from the catalogue (§6.10) into the Events reference book.
- Log lines and metric samples, which are PSPU §3's. This chapter says
  only how to tell them from events (§6.8).
- How the kernel's access-check interface accepts and copies an audit
  context. This chapter says what a component passes (§6.7); the
  interface is described in the Peios Kernel TRM.

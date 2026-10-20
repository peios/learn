---
title: Interpreting Events
type: concept
description: Read event definitions alongside their transport, identity evidence, and delivery limits.
related:
  - peios/reading-records/evman
  - peios/reading-records/stored-records
---

An event records an observation: an access check completed, a service
started, or a package changed. Its type identifies the observation, and its
fields describe it. Read the definition before drawing conclusions from a
record or from its absence.

## Find the definition

Each component supplies event and field definitions in `.evman` files under
`/usr/share/evman`. The [event manual](~peios/reading-records/evman) reads those
installed definitions. Consult the catalog shipped with the producer's
version when interpreting older records.

An event definition describes its trigger, tier, field presence, and any
meaning specific to that event. A field definition supplies its general
type and vocabulary. A group names fields that travel together. The catalog
can define fields that no current event carries; a definition alone is not
proof that a producer writes the field.

The [catalog format](~specifications/pgss/events/the-catalogue) defines how
components maintain these records. Event and field lookup belongs to the
catalog, rather than a separately maintained table in Learn.

Some components also describe their events in their manuals, where an
event's meaning depends on the mechanism behind it:

- The kernel's access control subsystem describes its audit records in
  [Event Families and
  Delivery](~kernel/kacs/auditing/event-families-and-delivery). The
  registry's [Audit](~kernel/lcs/security/audit) page and StrataFS's
  [Audit](~kernel/stratafs/security/audit) page describe theirs. The
  kernel's [Emission
  Policy](~kernel/internals/kmes/emission-policy) page describes how it
  decides which event types to write.
- eventd describes the events it writes about itself in [Synthetic Event
  Payloads](~peios/eventd/event-storage/synthetic-event-payloads).
- [Authentication Events](~peios/authentication/audit-events) describes the
  logon, attestation, and credential events of authd and lpsd.

## Identify the transport and origin

KMES carries kernel and userspace events in shared per-CPU rings. The kernel
adds the event's sequence, CPU, timestamp, and identity stamps. Userspace
chooses its event type and payload, so a kernel-looking type name does not
establish a kernel origin. Check `emitter.class` and distinguish the stamped
identity from identities asserted inside the payload.

`emitter.token.guid` identifies the effective token at emission;
`emitter.true-token.guid` identifies the primary token before impersonation.
`emitter.process.guid` identifies the process instance. A null identity stamp
must remain unknown. It does not identify a privileged caller. Read the
[kernel event model](~kernel/internals/kmes/event-model) for the stamp and
wire-layout contract.

Some records use other paths:

- eventd inserts its own operational events into its store. They have no
  KMES sequence or kernel-stamped emitter identity.
- LCS watch records report registry changes through a key file descriptor.
  They have their own [binary format](~kernel/internals/lcs/watches/event-records)
  and are notifications, not KMES events or an audit trail.
- Logs and metrics use separate ingestion paths and stores. Their
  [delivery guarantees](~peios/reading-records/stored-records) differ from
  event collection.

A KMES identity stamp is kernel attribution, not a cryptographic signature.
It does not authenticate the truth of an arbitrary payload or provide
non-repudiation for an exported record.

## Decode fields according to their definitions

A dotted payload path describes nested MessagePack maps: `subject.token.sid`
means the `sid` key inside `token` inside `subject`. It is not a literal
`subject.token.sid` key at the top level. A path cannot be both a value and a
container for other fields.

Read absence against the event's declared presence: required, optional, or
conditional. Do not replace an omitted value with zero, an empty string, or
nil. Required data missing from a record needs investigation; optional data
missing from it establishes no value.

Types carry units and wire representations. SIDs, GUIDs, and ACEs use binary
values; time and duration values use nanoseconds. Masks need their object
kind. Parallel arrays must be interpreted together. Resolve principal names
for display while preserving the original SIDs. The [value
conventions](~specifications/pgss/events/values) define the complete table.

Consumers should ignore unknown fields and retain unfamiliar values from
open enumerations. Closed enumerations and field types have stronger
contracts. The [extension rules](~specifications/pgss/events/extension)
distinguish additive changes from vocabulary changes that require a new
version. Successful transport decoding does not prove catalog conformance.

## Account for loss and ordering

A reader has its own position in each shared ring; it does not receive a
private buffer. Writers can overwrite unread events. Slow readers do not
block other readers or the producer, and overwritten records cannot be
recovered from KMES. A later attachment can still read records that remain
in the ring.

Sequence establishes order within a CPU for one boot. Keep CPU and boot
context with it. Wall-clock adjustments and different CPUs prevent timestamps
from establishing a total causal order across the machine.

eventd persists the records it receives and reports detected sequence gaps.
Collection, storage failure, retention, filtering, and authorization can all
limit what a query returns. Follow the [missing-record
workflow](~peios/reading-records/finding-missing-records) before treating an
empty result or a gap in a filtered display as proof of what happened.

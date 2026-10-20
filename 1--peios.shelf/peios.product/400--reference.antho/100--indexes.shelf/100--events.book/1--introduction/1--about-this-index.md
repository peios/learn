---
title: About This Index
description: What the index lists, how to read an event page, where event
  definitions come from, and where events without a chapter here are
  documented.
---

The Peios Events Index lists event types that Peios components emit, with
the fields each one carries. Use it to look up what a record means after you
have found it, for example in eventd's store. Where an event's meaning
depends on the mechanism behind it, the event's page links to the guide or
manual that describes that mechanism.

## Chapters

Each chapter covers the event types of one component, with one page per
event type. The index has these chapters:

| Chapter | Component | Event types |
|---|---|---|
| [Service Events](~peios/events/peinit/peinit-boot-downgraded) | peinit | `peinit.*` |
| [Time Events](~peios/events/timed/timed-clock-stepped) | timed | `timed.*` |
| [Network Configuration Events](~peios/events/netd/netd-hostname-changed) | netd | `netd.*` |
| [Trust Events](~peios/events/trustd/trustd-root-added) | trustd | `trustd.*` |
| [Desktop Server Events](~peios/events/gxwid/gxwid-certificate-renewed) | gxwid | `gxwid.*` |

## Reading an event page

Each event page describes what the event records and lists the event's
metadata:

- **Event type:** the name the record carries in `event.type`.
- **Defined in:** the `.evman` fragment that defines the type.
- **Tier:** whether the type is recorded by default. An `essential` type is
  always recorded. A `standard` type is recorded unless the emission policy
  switches it off, and a `verbose` or `debug` type only when the policy
  switches it on
  ([PGSS §6.8](~specifications/pgss/events/events-logs-and-tiers)).
- **Gating:** what else decides which occurrences are recorded. A gated type
  is recorded only when both the emission policy and its gating ask for the
  occurrence ([PGSS §6.9](~specifications/pgss/events/emission-policy)).
- **Cardinality:** how many records one occurrence produces, where that is
  not one.

The fields table that follows lists each payload field with its type, its
presence and its meaning. Presence is `required`, `optional`, or `when`
followed by a condition on another field. An emitter leaves out a field it
has no value for, so read an absent field against its presence rather than
as a signal of its own.

Every record also carries the header fields that the kernel's event stream
adds, such as `event.time` and `emitter.class`, described in the kernel's
[Event Model](~kernel/internals/kmes/event-model). Payloads don't repeat
them, so the fields tables leave them out.

## Where the definitions come from

Each event type and field is defined in the evman catalog: the `.evman`
fragments that components install in `/usr/share/evman/` ([PGSS
§6.10](~specifications/pgss/events/the-catalogue)). The pages in this index
restate those definitions, and the fragment is the authority when the two
differ. On a running system, [`evman`](~peios/reading-records/evman) prints
a definition from the installed fragments.

New event types, new fields, and new values of open enumerations are additive
changes ([PGSS §6.11](~specifications/pgss/events/extension)). A consumer
that keeps fields it doesn't know, and treats an unknown value of an open
enumeration as a value, keeps working when they arrive.

## Events documented elsewhere

Some components document their event types outside this index:

- **The kernel:** each subsystem's manual describes its audit records. The
  access control subsystem's are in [Event Families and
  Delivery](~kernel/kacs/auditing/event-families-and-delivery), the
  registry's in its [Audit](~kernel/lcs/security/audit) page, and the
  StrataFS filesystem's in its [Audit](~kernel/stratafs/security/audit)
  page. The kernel's [Emission
  Policy](~kernel/internals/kmes/emission-policy) page describes how it
  decides which of its event types to write.
- **eventd:** the five event types eventd writes about itself are in
  [Synthetic Event
  Payloads](~peios/eventd/event-storage/synthetic-event-payloads).
- **authd and lpsd:** [Authentication
  Events](~peios/authentication/audit-events) describes the logon,
  attestation, and credential events.

Registry watch records are not KMES events and never reach eventd's store.
A watcher reads them from a key's file descriptor, and the kernel's [Event
Records](~kernel/lcs/watches/event-records) page describes their layout.

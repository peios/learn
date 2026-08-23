---
title: Per-Field Control
description: Granting some fields of a record and not others through object ACEs — how field GUIDs are derived rather than registered.
---

A descriptor can grant read access to some fields of a record and not
others, using KACS **object ACEs** and object type lists. A caller
authorized for a pattern but not for a field receives the records with
that field absent — indistinguishable from a record that never carried
it (PSPU §3.28).

## Object type lists

For each access check eventd builds an object type list: a two-level
tree with the data type's root at level 0 and one field per node at
level 1.

```text
Level 0: root GUID for the data type
  Level 1: timestamp
  Level 1: event_type
  Level 1: cpu_id
  Level 1: origin_class
  Level 1: effective_token_guid
  Level 1: true_token_guid
  Level 1: process_guid
  Level 1: granted_access
  Level 1: target_sid
  Level 1: source.name
```

`kacs_access_check_list` returns a verdict per node, and eventd uses
them to include or exclude each field.

The three root GUIDs — one for events, one for logs, one for metrics —
are in §B.

## Field GUIDs are derived, not registered

A field's GUID is computed deterministically with UUID v5 (RFC 4122):

```text
field_guid = uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)
```

with the namespace UUID in §B, and `field_name` the field's
query-language name as UTF-8.

There is **no registry of field GUIDs and no allocation step**. The same
name always yields the same GUID, so an administrator writing a
descriptor computes the GUID from the field name with the same algorithm
that eventd will use when it builds the list. This is the one part of
eventd's access control that a third party reproduces rather than merely
consumes.

Derivation rather than registration is what makes payload fields
tractable at all: event payload schemas belong to the emitting
subsystems, eventd has no catalogue of them, and a new event type
carrying a new field needs no registration anywhere before a descriptor
can name it.

Which names are used:

| Data | `field_name` |
|---|---|
| Event header field | the column name — `timestamp`, `event_type`, `cpu_id` |
| Event payload field | the flattened dot path — `granted_access`, `target_sid`, `source.name` |
| Log field | the column name — `origin`, `message`, `is_error` |
| Fixed metric field | `timestamp`, `boot_id`, `name`, `type`, `value` |
| Metric label | the label key — `core`, `device` |

Payload fields suppressed by flattening or by a header collision are not
query-language fields, so they get no GUID (PSPU §3.22). Metric label
keys cannot collide with the fixed metric fields, because ingestion
rejects records whose labels do.

## The GUID does not encode scope

A field GUID names a field and nothing else. `granted_access` produces
the same GUID whatever event type carries it.

Scoping comes from the descriptor hierarchy: an object ACE naming the
`granted_access` GUID inside the descriptor for pattern `kacs` means
"the `granted_access` field of KACS events". The same ACE in a different
pattern's descriptor means the same field of that pattern's records.

## Writing one

An object ACE with **no** object type GUID applies to the root and
therefore to every field. One **with** a field GUID applies to that
field.

To grant a security team full read access to KACS events, and a
monitoring team only the timestamp, type and CPU:

- Allow SecurityAdmins, `EVENTD_READ`, no object GUID
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `timestamp`
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `event_type`
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `cpu_id`

MonitoringTeam querying KACS events receives records containing exactly
those three keys. Payload fields, identity GUIDs and the remaining
header fields are absent.

## Building the list per record

The list is constructed from the fields actually present in the record
being checked: the root node, then a level-1 node per field.

**Event records** contribute every header field plus every non-suppressed
flattened payload field present in that particular payload. Different
event types produce different lists, because they carry different
payloads — and two events of the same type can too, since a payload is
opaque MessagePack and nothing requires two of a type to agree.

**Log records** have a fixed field set — `timestamp`, `origin`,
`is_error`, `message`, `job_id`, `boot_id` — so the list is the same for
every log record.

**Metric records** contribute the five fixed fields plus the series'
label keys, which vary per series.

Derived aggregate outputs — `count`, `sum`, `avg`, `min`, `max` — are
omitted from the list entirely. They are not source fields, have no GUID
and no access identity of their own, and are visible when the caller is
authorized for the records and source fields they were computed from
(PSPU §3.28).

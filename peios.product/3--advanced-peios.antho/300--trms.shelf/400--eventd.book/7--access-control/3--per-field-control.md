---
title: Per-Field Control
description: Granting some fields of a record and not others through object ACEs — how field GUIDs are derived rather than registered.
---

A descriptor can grant read access to some fields of a record and not
others, using KACS **object ACEs** and object type lists.
[*fieldaccess.a-descriptor-can-grant-some-fields-of-a-record-and-not-others]
A caller
authorized for a pattern but not for a field receives the records with
that field absent — indistinguishable from a record that never carried
it (PSPU §3.28).
[*fieldaccess.an-unauthorized-field-is-absent-as-if-never-carried]

## Object type lists

For each access check eventd builds an object type list: a two-level
tree with the data type's root at level 0 and one field per node at
level 1.
[*fieldaccess.the-object-type-list-is-the-type-root-at-level-0-and-one-field-per-level-1-node]

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
[*fieldaccess.each-field-is-included-or-excluded-by-its-node-verdict]

The three root GUIDs — one for events, one for logs, one for metrics —
are in §B.

## Field GUIDs are derived, not registered [*fieldaccess.field-guids-are-derived-not-registered]

A field's GUID is computed deterministically with UUID v5 (RFC 4122):

```text
field_guid = uuid_v5(EVENTD_FIELD_NAMESPACE, field_name)
```

with the namespace UUID in §B, and `field_name` the field's
query-language name as UTF-8.
[*fieldaccess.a-field-guid-is-uuid-v5-of-the-utf-8-field-name-in-the-eventd-namespace]

There is **no registry of field GUIDs and no allocation step**. The same
name always yields the same GUID, so an administrator writing a
descriptor computes the GUID from the field name with the same algorithm
that eventd will use when it builds the list.
[*fieldaccess.the-same-field-name-always-yields-the-same-guid] This is the one part of
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
| Event header field | the column name — `timestamp`, `event_type`, `cpu_id` [*fieldaccess.an-event-header-field-is-named-by-its-column-name] |
| Event payload field | the flattened dot path — `granted_access`, `target_sid`, `source.name` [*fieldaccess.an-event-payload-field-is-named-by-its-flattened-dot-path] |
| Log field | the column name — `origin`, `message`, `is_error` [*fieldaccess.a-log-field-is-named-by-its-column-name] |
| Fixed metric field | `timestamp`, `boot_id`, `name`, `type`, `value` [*fieldaccess.the-fixed-metric-field-names] |
| Metric label | the label key — `core`, `device` [*fieldaccess.a-metric-label-is-named-by-its-label-key] |

Payload fields suppressed by flattening or by a header collision are not
query-language fields, so they get no GUID (PSPU §3.22).
[*fieldaccess.suppressed-payload-fields-get-no-guid] Metric label
keys cannot collide with the fixed metric fields, because ingestion
rejects records whose labels do.

## The GUID does not encode scope

A field GUID names a field and nothing else. `granted_access` produces
the same GUID whatever event type carries it.
[*fieldaccess.a-field-guid-does-not-depend-on-the-event-type-carrying-it]

Scoping comes from the descriptor hierarchy: an object ACE naming the
`granted_access` GUID inside the descriptor for pattern `kacs` means
"the `granted_access` field of KACS events". The same ACE in a different
pattern's descriptor means the same field of that pattern's records.
[*fieldaccess.a-field-ace-is-scoped-by-the-pattern-descriptor-holding-it]

## Writing one

An object ACE with **no** object type GUID applies to the root and
therefore to every field.
[*fieldaccess.an-object-ace-without-a-guid-applies-to-every-field] One
**with** a field GUID applies to that field.
[*fieldaccess.an-object-ace-with-a-field-guid-applies-to-that-field]

To grant a security team full read access to KACS events, and a
monitoring team only the timestamp, type and CPU:

- Allow SecurityAdmins, `EVENTD_READ`, no object GUID
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `timestamp`
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `event_type`
- Allow MonitoringTeam, `EVENTD_READ`, object GUID = `cpu_id`

MonitoringTeam querying KACS events receives records containing exactly
those three keys. Payload fields, identity GUIDs and the remaining
header fields are absent.
[*fieldaccess.a-grant-of-three-field-guids-yields-records-with-exactly-those-three-keys]

## Building the list per record

The list is constructed from the fields actually present in the record
being checked: the root node, then a level-1 node per field.
[*fieldaccess.the-list-is-built-from-the-fields-present-in-the-record]

**Event records** contribute every header field plus every non-suppressed
flattened payload field present in that particular payload.
[*fieldaccess.an-event-list-has-every-header-field-and-every-present-unsuppressed-payload-field]
Different
event types produce different lists, because they carry different
payloads — and two events of the same type can too, since a payload is
opaque MessagePack and nothing requires two of a type to agree.
[*fieldaccess.two-events-of-the-same-type-can-produce-different-lists]

**Log records** have a fixed field set — `timestamp`, `origin`,
`is_error`, `message`, `job_id`, `boot_id` — so the list is the same for
every log record. [*fieldaccess.every-log-record-has-the-same-six-field-list]

**Metric records** contribute the five fixed fields plus the series'
label keys, which vary per series.
[*fieldaccess.a-metric-list-has-the-five-fixed-fields-and-the-series-label-keys]

Derived aggregate outputs — `count`, `sum`, `avg`, `min`, `max` — are
omitted from the list entirely.
[*fieldaccess.aggregate-outputs-are-omitted-from-the-list] They are not
source fields, have no GUID
and no access identity of their own, and are visible when the caller is
authorized for the records and source fields they were computed from
(PSPU §3.28).
[*fieldaccess.an-aggregate-is-visible-when-its-source-records-and-fields-are-authorized]

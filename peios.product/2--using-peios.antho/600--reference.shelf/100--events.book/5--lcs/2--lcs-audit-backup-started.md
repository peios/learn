---
title: "lcs.audit.backup.started"
description: "The record that a registry subtree backup began, emitted before any data is read."
---

- **Event type:** `lcs.audit.backup.started`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** none — audited unconditionally
- **Cardinality:** one record per occurrence

The record that a registry subtree backup began, emitted **before any data
is read**. Backup is a privilege-gated bulk operation that bypasses
per-key access checks entirely, so this trail is the only evidence it
happened at all — which is why it is audited whatever the target key's
SACL says.

The start record exists so that an operation dying partway still leaves
evidence that it began. A start with no matching end is itself the
finding.

Emission failure fails the operation with `EIO`, unlike every other LCS
event: an unrecorded bulk read of the configuration store is not permitted
to proceed.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`caller`](~peios/events/groups/group-caller) | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`caller`](~peios/events/groups/group-caller) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`caller`](~peios/events/groups/group-caller) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`caller`](~peios/events/groups/group-caller) | The impersonation level of the effective token. |
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | required | The registry key an operation acted on. |
| [`operation.fd`](~peios/events/field-index/fields-operation#operation.fd) | `uint` | required | The descriptor the backup stream was written to. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

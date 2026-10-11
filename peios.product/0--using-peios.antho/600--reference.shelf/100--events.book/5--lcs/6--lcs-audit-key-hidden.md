---
title: "lcs.audit.key.hidden"
description: "The record that a registry key was hidden in a layer through its own handle, or that an attempt failed."
---

- **Event type:** `lcs.audit.key.hidden`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** DELETE overlaps the alarm mask cached on the key handle
- **Cardinality:** once per hide through a handle whose mask covers it

The record that a registry key was hidden in a layer through its own
handle, or that an attempt failed. Hiding writes a marker that masks the
key in every lower layer without deleting it there, so to every reader the
key is gone; it is gated on `DELETE`, as deleting is.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`caller`](~peios/events/groups/group-caller) | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`caller`](~peios/events/groups/group-caller) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`caller`](~peios/events/groups/group-caller) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`caller`](~peios/events/groups/group-caller) | The impersonation level of the effective token. |
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `key`. |
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | required | The registry key an operation acted on. |
| [`object.key.path`](~peios/events/field-index/fields-object#object.key.path) | `str` | required | The resolved absolute path of the registry key, in canonical form, such as `Machine\System\KMES`. |
| [`object.key.layer.name`](~peios/events/field-index/fields-object#object.key.layer.name) | `str` | optional | The layer the marker was written in. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | Always `DELETE`. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | The access mask in force. |
| [`access.matched`](~peios/events/field-index/fields-access#access.matched) | `uint.mask` | required | The subset of the requested access that overlapped an audit mask and therefore caused the record to exist. |
| [`access.audit-mask`](~peios/events/field-index/fields-access#access.audit-mask) | `uint.mask` | required | The full continuous-audit mask cached on a handle, of which `access.matched` is the part this operation touched. |
| [`mutation.sequence`](~peios/events/field-index/fields-mutation#mutation.sequence) | `uint` | optional | The sequence number LCS stamped on a registry mutation. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | The transaction the operation belonged to, registry or package. |
| [`request.timed-out`](~peios/events/field-index/fields-request#request.timed-out) | `bool` | when `outcome.success == false` | Whether a request's wait for the source's reply ran out before the reply arrived. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

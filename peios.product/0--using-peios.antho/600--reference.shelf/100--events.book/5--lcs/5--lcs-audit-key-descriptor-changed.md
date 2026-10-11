---
title: "lcs.audit.key.descriptor.changed"
description: "The record that a registry key's security descriptor was changed through a key handle, or that an attempt failed."
---

- **Event type:** `lcs.audit.key.descriptor.changed`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** always when the change includes the SACL; otherwise WRITE_DAC or WRITE_OWNER overlaps the alarm mask cached on the key handle
- **Cardinality:** once per descriptor change it covers

The record that a registry key's security descriptor was changed through a
key handle, or that an attempt failed.

**A change to the SACL is always recorded**, whatever the handle's mask.
It takes `ACCESS_SYSTEM_SECURITY`, which only `SeSecurityPrivilege` grants,
such changes are rare, and removing a SACL is exactly how someone hides
what follows. It is recorded once the handle's own access check admits it:
a caller whose handle lacks `ACCESS_SYSTEM_SECURITY` is refused before any
record, so asking for a SACL change cannot be used to write records.
Owner, group and DACL changes follow the handle's mask, as writes do.

Both descriptors are recorded by length, SHA-256 digest and owner, never
in full. Whether the SACL was part of the change is
`object.sd.components`.

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
| [`object.sd.components`](~peios/events/field-index/fields-object#object.sd.components) | `uint.flags` | required | The parts the caller asked to change, its `security_info`. |
| [`object.sd.length`](~peios/events/field-index/fields-object#object.sd.length) | `uint.bytes` | optional | The descriptor as written: the merge of the caller's parts into the old one. Absent when the request failed before the merge. |
| [`object.sd.length-previous`](~peios/events/field-index/fields-object#object.sd.length-previous) | `uint.bytes` | optional | Absent when the request failed before the old descriptor was read. |
| [`object.sd.digest`](~peios/events/field-index/fields-object#object.sd.digest) | `bin` | optional | Present with `object.sd.length`. |
| [`object.sd.digest-previous`](~peios/events/field-index/fields-object#object.sd.digest-previous) | `bin` | optional | Present with `object.sd.length-previous`. |
| [`object.sd.owner`](~peios/events/field-index/fields-object#object.sd.owner) | `bin.sid` | optional | Present with `object.sd.length`. |
| [`object.sd.owner-previous`](~peios/events/field-index/fields-object#object.sd.owner-previous) | `bin.sid` | optional | Present with `object.sd.length-previous`. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | The rights the change needs: `WRITE_OWNER` for the owner or group, `WRITE_DAC` for the DACL, `ACCESS_SYSTEM_SECURITY` for the SACL. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | The access mask in force. |
| [`access.matched`](~peios/events/field-index/fields-access#access.matched) | `uint.mask` | required | Zero when the record exists only because the change included the SACL. |
| [`access.audit-mask`](~peios/events/field-index/fields-access#access.audit-mask) | `uint.mask` | required | The full continuous-audit mask cached on a handle, of which `access.matched` is the part this operation touched. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | The transaction the operation belonged to, registry or package. |
| [`request.timed-out`](~peios/events/field-index/fields-request#request.timed-out) | `bool` | when `outcome.success == false` | True when the source did not answer in time, so the change may have been applied after all. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

---
title: "lcs.audit.key.created"
description: "The record that a registry key was created."
---

- **Event type:** `lcs.audit.key.created`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** a matching SACL audit ACE on the parent key, for KEY_CREATE_SUB_KEY
- **Cardinality:** once per key created

The record that a registry key was created. Creating a key checks only
`KEY_CREATE_SUB_KEY` on its parent, so the parent's SACL decides, by the
rule `lcs.audit.key.opened` applies to an open: a success audit ACE on the
parent that matches the caller. No handle exists yet to carry an alarm
mask.

Only a key that was made is recorded. A create that found the key already
there and opened it instead writes nothing here; it is an open, and
`lcs.audit.key.opened` records it if the key's own SACL asks. The record
is written once the key exists, so a create whose handle then fails to
reach the caller is still recorded, because the key was still made. A
transacted create is recorded when staged.

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
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | required | The new key. |
| [`object.key.path`](~peios/events/field-index/fields-object#object.key.path) | `str` | required | The new key's full path. |
| [`object.key.layer.name`](~peios/events/field-index/fields-object#object.key.layer.name) | `str` | optional | The layer the key was created in. |
| [`object.key.created`](~peios/events/field-index/fields-object#object.key.created) | `bool` | required | Always true. |
| [`object.key.volatile`](~peios/events/field-index/fields-object#object.key.volatile) | `bool` | required | Whether a registry key is volatile, meaning it lives only in memory and does not survive a reboot. |
| [`object.key.volatile-requested`](~peios/events/field-index/fields-object#object.key.volatile-requested) | `bool` | required | Equal to `object.key.volatile`, since only a key that was made is recorded. |
| [`object.key.symlink`](~peios/events/field-index/fields-object#object.key.symlink) | `bool` | required | Whether a registry key is a symbolic link to another key. |
| [`object.sd.length`](~peios/events/field-index/fields-object#object.sd.length) | `uint.bytes` | required | The new key's descriptor, as built from the parent's inheritable ACEs and the caller's token. |
| [`object.sd.owner`](~peios/events/field-index/fields-object#object.sd.owner) | `bin.sid` | optional | The owner SID on the object's security descriptor. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | Always `KEY_CREATE_SUB_KEY`, the right checked on the parent. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | What the parent check granted. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | The transaction the operation belonged to, registry or package. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Always true. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

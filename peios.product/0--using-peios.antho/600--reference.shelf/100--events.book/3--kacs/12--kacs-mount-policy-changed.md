---
title: "kacs.mount.policy.changed"
description: "The record that a filesystem's KACS mount policy was set: what happens to an object on it that has no stored descriptor."
---

- **Event type:** `kacs.mount.policy.changed`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** none — every change a caller admitted by the volume-management gate makes is recorded
- **Cardinality:** once per change

The record that a filesystem's KACS mount policy was set: what happens to an
object on it that has no stored descriptor. `unmanaged` turns access control
off for the whole filesystem; `deny-missing` refuses such objects; the two
`synthesize` policies build a descriptor from the parent and the template
the caller supplies.

Setting a policy needs SeManageVolumePrivilege or SeTcbPrivilege. Every
other refusal comes before that check, so a record is always of a change
made.

**The record does not carry the template.** A synthesising policy's template
descriptor decides what every unlabelled object on the filesystem grants;
read it back with `kacs_get_mount_policy`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`subject`](~peios/events/groups/group-subject) | The user SID of the effective token the operation ran under. |
| [`subject.token.groups`](~peios/events/field-index/fields-subject#subject.token.groups) | `bin.sid[]` | via [`subject`](~peios/events/groups/group-subject) | The group SIDs carried by the effective token. |
| [`subject.token.group-attributes`](~peios/events/field-index/fields-subject#subject.token.group-attributes) | `uint.flags[]` | via [`subject`](~peios/events/groups/group-subject) | Per-group attribute bitmasks, positionally parallel to `subject.token.groups`. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`subject`](~peios/events/groups/group-subject) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`subject`](~peios/events/groups/group-subject) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`subject`](~peios/events/groups/group-subject) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`subject`](~peios/events/groups/group-subject) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`subject`](~peios/events/groups/group-subject) | The impersonation level of the effective token. |
| [`subject.token.uid`](~peios/events/field-index/fields-subject#subject.token.uid) | `uint` | via [`subject`](~peios/events/groups/group-subject) | The Linux UID this token projects onto, for correlating a Peios event with Linux-side audit data. |
| [`emitter.process.pid`](~peios/events/field-index/fields-emitter#emitter.process.pid) | `uint` | via [`subject`](~peios/events/groups/group-subject) | The process ID the record was written from. |
| [`emitter.process.name`](~peios/events/field-index/fields-emitter#emitter.process.name) | `str` | via [`subject`](~peios/events/groups/group-subject) | The kernel's name for the emitting process, typically the executable's basename. |
| [`emitter.process.executable`](~peios/events/field-index/fields-emitter#emitter.process.executable) | `str.path` | via [`subject`](~peios/events/groups/group-subject) | The path the emitting process was executed from, resolved at exec with symbolic links already followed. |
| [`subject.pip.type`](~peios/events/field-index/fields-subject#subject.pip.type) | `uint.enum` | via [`subject`](~peios/events/groups/group-subject) | The Protected Isolated Process type in force for the access check. |
| [`subject.pip.trust`](~peios/events/field-index/fields-subject#subject.pip.trust) | `uint` | via [`subject`](~peios/events/groups/group-subject) | The PIP trust level in force for the access check. |
| [`object.mount.fs-type`](~peios/events/field-index/fields-object#object.mount.fs-type) | `str` | optional | The filesystem's type, when the kernel knows it. |
| [`object.mount.policy`](~peios/events/field-index/fields-object#object.mount.policy) | `str.enum` | required | The KACS mount policy in force, which decides what happens to an object with no stored descriptor. |
| [`object.mount.policy-previous`](~peios/events/field-index/fields-object#object.mount.policy-previous) | `str.enum` | required | The mount policy a change replaced, beside `object.mount.policy`, the one it put in force. |
| [`object.mount.policy-generation`](~peios/events/field-index/fields-object#object.mount.policy-generation) | `uint` | required | The generation the change began. Every descriptor cached under an older one is discarded on its next use. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Always true: every refusal is decided before anything changes. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

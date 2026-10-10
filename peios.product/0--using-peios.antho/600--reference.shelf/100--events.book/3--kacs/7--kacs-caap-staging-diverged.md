---
title: "kacs.caap.staging.diverged"
description: "The record that a staged central access policy would have decided an access differently from the policy in force."
---

- **Event type:** `kacs.caap.staging.diverged`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** a staged central access policy applies to the object, and its result differs from the effective one
- **Cardinality:** once per access check

The record that a staged central access policy would have decided an
access differently from the policy in force. The access itself is decided
by the effective policy alone; this records what promoting the staged one
would change, for this subject and this object.

It is the event to watch while trialling a policy: stage it, let the
system run, and read these records to see who would gain or lose access
before anyone does. **It is silent unless a staged policy exists**, so on
most systems it never fires.

The difference is not always in the grant. Staged and effective
evaluation also differ when the per-object results of an object-type
check differ, or when the audit records the two would produce differ, so
a record can carry equal `access.granted` and `access.granted-staged`.

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
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | What sort of thing the operation acted on. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | when `object.kind == file` | The absolute path of the file the operation acted on, resolved at the enforcement point. |
| [`object.process.pid`](~peios/events/field-index/fields-object#object.process.pid) | `uint` | when `object.kind == process` | The process ID of the process the operation acted on. |
| [`object.process.guid`](~peios/events/field-index/fields-object#object.process.guid) | `bin.guid` | when `object.kind == process` | The durable GUID of the process the operation acted on. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | when `object.kind == token` | The LUID of the token the operation acted on, for token-open and token-adjust checks. |
| [`object.token.guid`](~peios/events/field-index/fields-object#object.token.guid) | `bin.guid` | when `object.kind == token` | The durable GUID of the token the operation acted on. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | The access mask the caller asked for, after generic bits have been mapped to type-specific ones. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | What the effective policy granted: the access the caller actually got. |
| [`access.granted-staged`](~peios/events/field-index/fields-access#access.granted-staged) | `uint.mask` | required | What the staged policy would have granted instead. |
| [`fields.attestation.userspace`](~peios/events/field-index/fields-fields#fields.attestation.userspace) | `bool` | optional | Set on every record of the AccessCheck syscall, and on no other. There the descriptor, and with it `trigger.ace`, is always the caller's, as are any audit context and PIP state it passes. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

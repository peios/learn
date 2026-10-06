---
title: "kacs.audit.access.checked"
description: "The record that an access check completed, and what it decided."
---

- **Event type:** `kacs.audit.access.checked`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** a matching SACL audit ACE, or the token's audit policy
- **Cardinality:** once per matching audit ACE, not once per access

The record that an access check completed, and what it decided. The most
common event on the system, and the one most investigations start from.

It fires against every kind of object KACS protects — files, processes,
tokens, sockets and SysV IPC objects — which is why `object.kind` is
required. A process opening another process, or a token adjusting another
token, puts an actor and an object of the same kind in one record, so the
`subject.` and `object.` fields are never interchangeable.

**It is silent by default.** Nothing is recorded unless an audit ACE in the
object's SACL matches, or the calling token's audit policy forces it. An
object with no SACL produces no record on any outcome, including denials.

**One access can produce several records.** The event is per matching audit
ACE, so an access matching three ACEs produces three records differing only
in `trigger.ace`.

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
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | The mask this check granted. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True when every requested bit is in `access.granted`. A `MAXIMUM_ALLOWED` request always reports true, because such a request returns whatever is available and cannot fail — so a success rate computed over these records is skewed by them. |
| [`trigger.kind`](~peios/events/field-index/fields-trigger#trigger.kind) | `str.enum` | required | Why an audit record exists at all. |
| [`trigger.ace`](~peios/events/field-index/fields-trigger#trigger.ace) | `bin.ace` | when `trigger.kind == sacl` | The exact ACE that caused this record, so a consumer can identify which rule fired. |
| [`fields.attestation.userspace`](~peios/events/field-index/fields-fields#fields.attestation.userspace) | `bool` | optional | Set when the check came through the access-check ioctl and its caller supplied the PIP state. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

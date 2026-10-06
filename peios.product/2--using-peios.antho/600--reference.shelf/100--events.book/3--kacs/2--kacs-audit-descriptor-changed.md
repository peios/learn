---
title: "kacs.audit.descriptor.changed"
description: "The record that a caller changed, or was authorised to change and failed to change, the security descriptor of a file, a token, a process or a System V IPC object."
---

- **Event type:** `kacs.audit.descriptor.changed`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** a change that includes the SACL, always; any other change when the rights it needed overlap the alarm mask on the handle it was made through
- **Cardinality:** once per authorised change

The record that a caller changed, or was authorised to change and failed to
change, the security descriptor of a file, a token, a process or a System V
IPC object. Registry keys have their own record of the same shape,
`lcs.audit.key.descriptor.changed`.

**A change to a SACL is always recorded**, whatever the old or new
descriptor says. Changing a SACL needs `ACCESS_SYSTEM_SECURITY`, which needs
SeSecurityPrivilege; it is rare; and removing one is how an intruder stops
being watched. Before this record existed a file's SACL could be removed in
silence, because the only audit of a descriptor change was evaluated
against the new SACL, which then had nothing in it.

Any other change — the owner, the group, the DACL, the integrity label — is
recorded when the rights it needed overlap the alarm mask on the handle it
was made through: the rule `kacs.audit.handle.used` follows. Only a file
handle carries such a mask, so for a token, a process or an IPC object only
a SACL change is recorded.

The descriptors themselves are not carried, only their SHA-256 digests,
lengths and owners. Equal digests mean the change rewrote the descriptor
without altering it.

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
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | `file`, `token`, `process` or `ipc`. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | optional | On a file, its absolute path, when the handle's path could be resolved. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | when `object.kind == token` | The LUID of the token the operation acted on, for token-open and token-adjust checks. |
| [`object.token.guid`](~peios/events/field-index/fields-object#object.token.guid) | `bin.guid` | when `object.kind == token` | The durable GUID of the token the operation acted on. |
| [`object.process.guid`](~peios/events/field-index/fields-object#object.process.guid) | `bin.guid` | when `object.kind == process` | The durable GUID of the process the operation acted on. |
| [`object.ipc.type`](~peios/events/field-index/fields-object#object.ipc.type) | `str.enum` | when `object.kind == ipc` | Which kind of System V IPC object the operation acted on: a semaphore set, a shared-memory segment or a message queue. |
| [`object.ipc.id`](~peios/events/field-index/fields-object#object.ipc.id) | `int` | when `object.kind == ipc` | The System V IPC identifier of the object, as `semget`, `shmget` or `msgget` returned it. |
| [`object.sd.components`](~peios/events/field-index/fields-object#object.sd.components) | `uint.flags` | required | The parts the caller set. A `SACL` bit means the record was not discretionary: such a change is always recorded. |
| [`object.sd.length`](~peios/events/field-index/fields-object#object.sd.length) | `uint.bytes` | when `outcome.success == true` | The byte length of the object's security descriptor. |
| [`object.sd.digest`](~peios/events/field-index/fields-object#object.sd.digest) | `bin` | when `outcome.success == true` | SHA-256 of the descriptor as written. |
| [`object.sd.owner`](~peios/events/field-index/fields-object#object.sd.owner) | `bin.sid` | optional | The owner of the descriptor written, when it has one. |
| [`object.sd.length-previous`](~peios/events/field-index/fields-object#object.sd.length-previous) | `uint.bytes` | optional | The byte length of the descriptor a change replaced. |
| [`object.sd.digest-previous`](~peios/events/field-index/fields-object#object.sd.digest-previous) | `bin` | optional | SHA-256 of the descriptor replaced. Absent, with its length and owner, where the object had no stored descriptor to replace. |
| [`object.sd.owner-previous`](~peios/events/field-index/fields-object#object.sd.owner-previous) | `bin.sid` | optional | The owner SID a change replaced. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | The rights the change needed: `WRITE_OWNER`, `WRITE_DAC`, `ACCESS_SYSTEM_SECURITY`, as the parts set ask. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | optional | What the handle the change was made through was opened with. Absent on a change made without one. |
| [`access.audit-mask`](~peios/events/field-index/fields-access#access.audit-mask) | `uint.mask` | optional | The alarm mask on that handle. |
| [`access.matched`](~peios/events/field-index/fields-access#access.matched) | `uint.mask` | optional | The part of `access.requested` the alarm mask matched, on a change made through a handle: zero when only the SACL made the record exist. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the new descriptor was written. A refused change — one the caller had no right to make — is not this record; it is the access check's. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

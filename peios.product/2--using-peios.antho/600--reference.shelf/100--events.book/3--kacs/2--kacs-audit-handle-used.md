---
title: "kacs.audit.handle.used"
description: "The record of what was done with a handle after it was opened."
---

- **Event type:** `kacs.audit.handle.used`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** the operation's required access overlaps the alarm mask cached on the handle
- **Cardinality:** once per operation on the handle

The record of what was done with a handle after it was opened. Where
`kacs.audit.access.checked` records the decision to open something, this
records each subsequent use of it.

The mask is configured by `SYSTEM_ALARM*` ACEs at the access check that
opened the handle, and the record is produced afterwards by whatever
enforcement point handles the operation. FACS, for file handles, is the
only such point today.

**The subject is re-read on every operation.** A handle outlives the token
that opened it, so a process that starts or stops impersonating keeps its
handles and every later operation is recorded under the token current at
that moment. An investigation assuming the open-time identity will
attribute later operations to the wrong principal.

Three masks appear together and are easy to confuse. Read as a sentence:
the operation needed `access.requested`, of which `access.matched`
triggered the audit, against a handle opened with `access.granted`, and it
succeeded or did not.

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
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `file` today, because FACS is the only enforcement point. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | required | The absolute path of the file the operation acted on, resolved at the enforcement point. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | Which operation was attempted.<br><br>Values here (open set): `file.access` · `file.mmap` · `file.mprotect` · `file.permission` · `file.write` · `file.ioctl` · `file.lock` · `file.fcntl` · `file.truncate` · `file.fallocate`. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | What this operation needs — a read needs `FILE_READ_DATA`, an `mmap` with `PROT_EXEC` needs `FILE_EXECUTE`. |
| [`access.matched`](~peios/events/field-index/fields-access#access.matched) | `uint.mask` | required | The subset of the requested access that overlapped an audit mask and therefore caused the record to exist. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | What the handle was opened with, not what this operation was granted. An operation can only succeed if `access.requested` is a subset of it. |
| [`access.audit-mask`](~peios/events/field-index/fields-access#access.audit-mask) | `uint.mask` | required | The full continuous-audit mask cached on a handle, of which `access.matched` is the part this operation touched. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation itself was allowed. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | From `KACS_FSR_*`, excluding `DECISION` (which names the ordinary path rather than a reason) and `AUDIT_EMIT_FAIL` (which cannot appear, being the failure of this record's own emission).<br><br>Values here (open set): `signed-exec` · `grant-deny` · `append-deny` · `unmanaged-sysfs`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

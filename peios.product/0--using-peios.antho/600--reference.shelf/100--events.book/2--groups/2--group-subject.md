---
title: "subject group"
description: "The security context an operation ran under, carried by every KACS event that has a causing principal."
---

- **Group:** `subject`
- **Defined in:** `kernel.evman`

The security context an operation ran under, carried by every KACS event
that has a causing principal. Three components: the effective token, the
process it ran in, and the PIP state in force.

The process is the emitter's, under `emitter.process`, because a kernel
access check runs in the caller's own context: the process that acted is
the process that wrote the record.

**The token and the process are different principals when impersonating.**
The token is the client's and the process is the server's, so reading the
pair as one identity will attribute a client's work to a server or the
reverse. `subject.token.type` is what tells you they have diverged.

The durable GUIDs are not repeated here. `emitter.token.guid`,
`emitter.true-token.guid` and `emitter.process.guid` ride in the event
header, so they are present on every event whether or not this group is.

Privileges, claims, the restricted-SID list, confinement state and the
default DACL are all deliberately absent. Each is unbounded and an event
embedding them could grow without limit. Code needing full token state
queries the token directly while it still exists; this group is for
correlation, not reconstruction.

## Fields

| Field | Type | Meaning |
|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | The user SID of the effective token the operation ran under. |
| [`subject.token.groups`](~peios/events/field-index/fields-subject#subject.token.groups) | `bin.sid[]` | The group SIDs carried by the effective token. |
| [`subject.token.group-attributes`](~peios/events/field-index/fields-subject#subject.token.group-attributes) | `uint.flags[]` | Per-group attribute bitmasks, positionally parallel to `subject.token.groups`. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | The impersonation level of the effective token. |
| [`subject.token.uid`](~peios/events/field-index/fields-subject#subject.token.uid) | `uint` | The Linux UID this token projects onto, for correlating a Peios event with Linux-side audit data. |
| [`emitter.process.pid`](~peios/events/field-index/fields-emitter#emitter.process.pid) | `uint` | The process ID the record was written from. |
| [`emitter.process.name`](~peios/events/field-index/fields-emitter#emitter.process.name) | `str` | The kernel's name for the emitting process, typically the executable's basename. |
| [`emitter.process.executable`](~peios/events/field-index/fields-emitter#emitter.process.executable) | `str.path` | The path the emitting process was executed from, resolved at exec with symbolic links already followed. |
| [`subject.pip.type`](~peios/events/field-index/fields-subject#subject.pip.type) | `uint.enum` | The Protected Isolated Process type in force for the access check. |
| [`subject.pip.trust`](~peios/events/field-index/fields-subject#subject.pip.trust) | `uint` | The PIP trust level in force for the access check. |

## Carried by

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.descriptor.changed`](~peios/events/kacs/kacs-audit-descriptor-changed)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.policy.changed`](~peios/events/kacs/kacs-caap-policy-changed)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected)
- [`kacs.impersonation.reverted`](~peios/events/kacs/kacs-impersonation-reverted)
- [`kacs.impersonation.started`](~peios/events/kacs/kacs-impersonation-started)
- [`kacs.mount.policy.changed`](~peios/events/kacs/kacs-mount-policy-changed)

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

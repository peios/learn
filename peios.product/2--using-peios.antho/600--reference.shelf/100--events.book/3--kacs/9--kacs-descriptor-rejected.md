---
title: "kacs.descriptor.rejected"
description: "The record that KACS read an object's stored security descriptor, found it corrupt, and refused to use it."
---

- **Event type:** `kacs.descriptor.rejected`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** none — every unreadable stored descriptor is recorded
- **Cardinality:** one record per occurrence

The record that KACS read an object's stored security descriptor, found it
corrupt, and refused to use it. The object is then treated as having a
descriptor nobody can satisfy, so every access to it is denied until the
descriptor is replaced by someone allowed to write one.

**This is often the only explanation for a sudden, universal denial.** A
file that everyone could open and nobody now can, with no change to its
descriptor anyone remembers making, is usually this: the stored bytes no
longer parse, whether from disk corruption, a tool writing the extended
attribute directly, or an interrupted write.

KACS records the event once per descriptor read, when the object's
descriptor cache is filled, not on every denied access that follows. The
subject is whoever's access made KACS read the descriptor: the first to
touch the file after it was cached, not whoever corrupted it.

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
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `file` today: file descriptors are the only stored descriptors KACS reads this way. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | optional | Not carried today. The descriptor is read through an anchor that has no mount, so no absolute path can be resolved at that point. |
| [`object.file.inode`](~peios/events/field-index/fields-object#object.file.inode) | `uint` | required | The inode number the object presents. |
| [`object.file.device`](~peios/events/field-index/fields-object#object.file.device) | `uint` | required | With `object.file.inode`, what names the file in place of a path: find it with `find <mount> -xdev -inum <inode>` on the filesystem of that device. |
| [`object.sd.length`](~peios/events/field-index/fields-object#object.sd.length) | `uint.bytes` | required | The length of the stored attribute that failed: 0 when it was empty, and more than 65,535 when it was too long to be a descriptor at all. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | Why the descriptor was refused. `corrupt` is the only reason today.<br><br>Values here (open set): `corrupt`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

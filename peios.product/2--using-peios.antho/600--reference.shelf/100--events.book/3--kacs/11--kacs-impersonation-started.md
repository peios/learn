---
title: "kacs.impersonation.started"
description: "The record that a thread took on, or tried to take on, a client's identity by impersonating its token."
---

- **Event type:** `kacs.impersonation.started`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** none — every impersonation attempt that names a client token is recorded
- **Cardinality:** once per attempt

The record that a thread took on, or tried to take on, a client's identity
by impersonating its token. The subject is the server — the token that
acted, as it stood before the switch — and the object is the client token.
Successes and refusals are both recorded.

Impersonation is per thread, so `emitter.thread.tid` names the thread that
changed identity, not `emitter.process.pid`. Records the thread writes
afterwards carry the client's token in their header, until a
`kacs.impersonation.reverted` record ends it.

**The level can be lowered without the attempt failing.**
`object.token.impersonation` is the level the client token offered, and
`object.token.impersonation-permitted` the level KACS let the server have.
Where the second is lower — the server lacked SeImpersonatePrivilege for a
different user, or the client's integrity was above the server's — the
impersonation succeeded at Identification, which can query the client's
identity but not act as it.

**The GUID is the installed token's.** A lowered level installs a new token,
so `object.token.guid` and `object.token.id` on a success are that token's,
and they match the `emitter.token.guid` of the thread's later records.
Exactly when the level was lowered they differ from the GUID of the token
the client handed over.

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
| [`emitter.thread.tid`](~peios/events/field-index/fields-emitter#emitter.thread.tid) | `uint` | required | The thread that wrote the record, where the operation is scoped to a thread rather than to its process. |
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `token`. |
| [`object.token.guid`](~peios/events/field-index/fields-object#object.token.guid) | `bin.guid` | required | The durable GUID of the token the operation acted on. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | required | The LUID of the token the operation acted on, for token-open and token-adjust checks. |
| [`object.token.sid`](~peios/events/field-index/fields-object#object.token.sid) | `bin.sid` | required | The client: whose identity the server took on or asked for. |
| [`object.token.type`](~peios/events/field-index/fields-object#object.token.type) | `str.enum` | required | `primary` only on a refusal: a primary token cannot be impersonated. |
| [`object.token.integrity`](~peios/events/field-index/fields-object#object.token.integrity) | `uint.integrity` | required | The integrity level of the token the operation acted on, as an integrity RID. |
| [`object.token.auth-id`](~peios/events/field-index/fields-object#object.token.auth-id) | `uint.luid` | optional | Absent only for a token with no logon session. |
| [`object.token.restricted`](~peios/events/field-index/fields-object#object.token.restricted) | `bool` | required | Whether the token is restricted: whether it carries restricting SIDs that every access check must also satisfy. |
| [`object.token.impersonation`](~peios/events/field-index/fields-object#object.token.impersonation) | `uint.enum` | required | The level the client token offered: the level asked for. |
| [`object.token.impersonation-permitted`](~peios/events/field-index/fields-object#object.token.impersonation-permitted) | `uint.enum` | optional | The level the gate allowed. Absent when the attempt was refused before the gate answered. |
| [`privilege.name`](~peios/events/field-index/fields-privilege#privilege.name) | `str.enum` | optional | `SeImpersonatePrivilege`, present when the server impersonated a different user, or across a restriction difference, and needed the privilege to do it at the level asked. The privilege is then marked used. |
| [`privilege.held`](~peios/events/field-index/fields-privilege#privilege.held) | `bool` | when `privilege.name == SeImpersonatePrivilege` | Always true where present: a server without the privilege is not refused but lowered to Identification, which `impersonation-permitted` shows. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | optional | On a refusal, where KACS knows why: the token handed over was a primary token (`EINVAL`); a restricted server tried to impersonate an unrestricted token of its own user, which would escape its restriction (`EPERM`); the token handle lacked `TOKEN_IMPERSONATE` (`EACCES`); or the identity could not be projected onto the thread's Linux credentials. Absent on a refusal for want of memory.<br><br>Values here (open set): `primary-token` · `restriction-escape` · `no-impersonate-access` · `projection-failed`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

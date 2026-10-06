---
title: "kacs.audit.privilege.used"
description: "The record that a privilege was spent."
---

- **Event type:** `kacs.audit.privilege.used`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** the token's audit policy, success and failure flavours independently; at a capability or volume gate, also the first use of that gate by the process under its current token, and never a CAP_OPT_NOAUDIT check
- **Cardinality:** once per privilege that contributed access; at a gate, once per process, token and gate

The record that a privilege was spent. Purely token-policy driven — no SACL
is involved, so there is no trigger to record. `operation.name` says where
it was spent, and the rest of the record follows from it.

`access-check` is a privilege that contributed access to an access check,
with whether that contribution survived. **Success there means the
privilege worked, not that it fired.** This is the field most often
misread. A false outcome is not a failed attempt to use a privilege; it is
a privilege that fired and was then overridden by a confinement, a CAAP
rule, or PIP non-dominance — usually the more interesting of the two
records, because it shows a boundary holding. **`MAXIMUM_ALLOWED` requests
produce nothing here.** Privilege-use auditing short-circuits on them, even
though SACL auditing was deliberately changed not to — a probing enumerator
therefore trips one and slips the other.

`linux-cap` is a privilege that satisfied a Linux capability check: KACS
answers every capability check with a privilege, and `linux.cap` names the
check. `volume-mount` is a privilege that satisfied the volume-management
gate the mount paths ask instead of `CAP_SYS_ADMIN`. **Each is recorded once
per process, token and gate**, not once per check: a TCB process makes
thousands of `CAP_SYS_ADMIN` checks a second, and the first answers who used
the privilege and for what. The set starts again when the process acts under
another token. Only successful uses are recorded, and only those of a user
process's own checks: a probe with `CAP_OPT_NOAUDIT`, a kernel thread's
check and a check against another process's credentials record nothing.
The record is written as the process returns to user space, so it follows
the system call that spent the privilege.

A token can carry either audit policy flavour, both, or neither, and each
governs its own outcome independently. **The boot SYSTEM token carries
`PRIVILEGE_USE_SUCCESS`**, so on a stock machine the records come from
SYSTEM and the services that inherit its token.

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
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | Which operation was attempted.<br><br>Values here (open set): `access-check` · `linux-cap` · `volume-mount`. |
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | optional | On an access check, the object checked. Absent at a gate, and on a check made through the AccessCheck syscall with no audit context: the kernel does not know what was checked. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | when `object.kind == file` | The absolute path of the file the operation acted on, resolved at the enforcement point. |
| [`object.process.pid`](~peios/events/field-index/fields-object#object.process.pid) | `uint` | when `object.kind == process` | The process ID of the process the operation acted on. |
| [`object.process.guid`](~peios/events/field-index/fields-object#object.process.guid) | `bin.guid` | when `object.kind == process` | The durable GUID of the process the operation acted on. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | when `object.kind == token` | The LUID of the token the operation acted on, for token-open and token-adjust checks. |
| [`object.token.guid`](~peios/events/field-index/fields-object#object.token.guid) | `bin.guid` | when `object.kind == token` | The durable GUID of the token the operation acted on. |
| [`privilege.name`](~peios/events/field-index/fields-privilege#privilege.name) | `str.enum` | required | The privilege a record is about, by its Windows name. |
| [`privilege.contributed`](~peios/events/field-index/fields-privilege#privilege.contributed) | `uint.mask` | when `operation.name == access-check` | The access bits this privilege supplied to the check, intersected with what the caller actually asked for. |
| [`privilege.surviving`](~peios/events/field-index/fields-privilege#privilege.surviving) | `uint.mask` | when `operation.name == access-check` | The subset of `privilege.contributed` that reached the final granted mask. |
| [`linux.cap`](~peios/events/field-index/fields-linux#linux.cap) | `str.enum` | when `operation.name == linux-cap` | The Linux capability whose check prompted the record, named as its `CAP_*` constant with the prefix removed, in kebab case: `CAP_NET_ADMIN` is `net-admin`. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | when `operation.name == access-check` | The whole check's requested mask, not this privilege's share of it. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | when `operation.name == access-check` | The whole check's final granted mask. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | On an access check, true when `privilege.surviving` is non-empty: derived rather than independently decided, and kept so that a single query for failed outcomes works across every event type. At a gate, always true. |
| [`fields.attestation.userspace`](~peios/events/field-index/fields-fields#fields.attestation.userspace) | `bool` | optional | Set on every record of the AccessCheck syscall, and on no other. There the descriptor, and with it `trigger.ace`, is always the caller's, as are any audit context and PIP state it passes. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

---
title: "kacs.caap.sacl.skipped"
description: "The record that a central access policy rule's SACL could not be parsed or evaluated, so the audit it asked for was skipped."
---

- **Event type:** `kacs.caap.sacl.skipped`
- **Defined in:** `kacs.evman`
- **Tier:** standard
- **Gating:** an access check that evaluates a central access policy rule whose SACL cannot be used
- **Cardinality:** once per rule whose SACL failed

The record that a central access policy rule's SACL could not be parsed or
evaluated, so the audit it asked for was skipped. The access decision is
unaffected — a rule's SACL only adds audit records — but the records that
rule should have produced for this access do not exist.

**This is the only evidence of the missing audit.** An administrator who
put an audit ACE in a policy rule expects records from every object the
policy covers; while the rule's SACL is broken, none arrive, and nothing
else says so.

A failure in a rule's staged SACL (`caap.phase` is `staged-sacl`) is
recorded too. It changes nothing in force, and is the warning that
promoting the staged policy would install a SACL that does not work.

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
| [`caap.policy.sid`](~peios/events/field-index/fields-caap#caap.policy.sid) | `bin.sid` | required | The SID identifying a central access policy. |
| [`caap.rule.index`](~peios/events/field-index/fields-caap#caap.rule.index) | `uint` | required | The zero-based position of a rule within the central access policy named by `caap.policy.sid`. |
| [`caap.phase`](~peios/events/field-index/fields-caap#caap.phase) | `str.enum` | required | Which phase of a central access policy's audit evaluation a CAAP diagnostic describes. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | `invalid-caap-sacl` means the SACL would not parse; `caap-sacl-evaluation-error` means it parsed and evaluating it failed.<br><br>Values here (open set): `invalid-caap-sacl` · `caap-sacl-evaluation-error`. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | The access mask the caller asked for, after generic bits have been mapped to type-specific ones. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | The effective grant of the check the rule was evaluated in. |
| [`access.granted-staged`](~peios/events/field-index/fields-access#access.granted-staged) | `uint.mask` | required | What a staged central access policy, not yet in force, would have granted. |
| [`fields.attestation.userspace`](~peios/events/field-index/fields-fields#fields.attestation.userspace) | `bool` | optional | Set when the check came through the access-check ioctl and its caller supplied the PIP state. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

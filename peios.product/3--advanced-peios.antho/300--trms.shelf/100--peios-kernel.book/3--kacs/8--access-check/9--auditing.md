---
title: Auditing in AccessCheck
description: Auditing is purely observational and never changes a decision — access, continuous and privilege-use auditing, and per-token policy.
---

Auditing is purely observational. No audit rule affects the access
decision, and audit ACEs are evaluated after the decision is final. [*check.auditing.observational]

Three mechanisms operate inside the pipeline, emitting two families of
KMES record: `access-audit` for object-access events from the SACL
walk and from token audit-policy forcing, and `privilege-use` for
privilege-use events. [*check.auditing.event-families] A third family, `caap-policy-diagnostic`, is
emitted for the CAAP conditions of §3.8.8 — a SACL evaluation error,
or a staged-versus-effective mismatch. [*check.auditing.caap-diagnostic-family] The event type strings and
payload schemas are in §3.C.

Event delivery happens before any result is written back to the
caller, and a failure to deliver fails the call. [*check.auditing.delivery-before-result] An audit event cannot
be suppressed by handing the syscall a bad output pointer.

## Access auditing

`SYSTEM_AUDIT` ACEs in the SACL define which attempts to log. Each
carries a SID, an access mask, and success and failure flags —
`SUCCESSFUL_ACCESS_ACE_FLAG` (0x40) and `FAILED_ACCESS_ACE_FLAG`
(0x80).

An event is emitted when the ACE's SID matches the caller, its mask
overlaps the requested access, and its flags match the outcome. [*check.auditing.audit-ace-conditions]

Two details matter. The SID is matched with **deny polarity** — the
broadest identity view, in which deny-only groups are visible —
because auditing should capture the widest possible picture rather
than the narrowest. [*check.auditing.deny-polarity-matching] And the overlap is tested against the
generic-mapped **requested** mask, not the final granted mask, so a
failed request is still auditable for the rights it actually asked
for. [*check.auditing.overlap-against-requested]

Conditional audit ACEs gate the event on an expression, using the same
deny-side membership polarity. An expression evaluating to UNKNOWN
emits the event: when in doubt, audit. [*check.auditing.unknown-condition-emits]

## Continuous auditing

Access auditing fires once, where AccessCheck runs. Continuous
auditing covers per-operation monitoring.

`SYSTEM_ALARM` ACEs configure it. When AccessCheck evaluates an alarm
ACE whose SID matches, the ACE's mask is accumulated into a
**continuous audit mask** returned to the caller, which stores it on
the open handle and enforces it per operation. [*check.auditing.alarm-accumulates-mask] Conditional alarm ACEs
use the same deny-side polarity as conditional audit ACEs. The alarm
branch deliberately performs no overlap test against the requested
mask — an alarm ACE contributes its mask on a SID match alone. [*check.auditing.alarm-no-overlap-test]

On each later operation the enforcement point emits a
`continuous-audit` event when the operation's normalised
required-access mask overlaps the stored mask. [*check.auditing.continuous-event-on-overlap] For FACS handles that
is the same mask used by the use-time check (§3.9.4). Where an
operation's authorization accepts any one of several rights — append
or write data, say — the required mask holds the accepted set and the
event records the subset that overlapped. [*check.auditing.continuous-records-overlapping-subset]

Events are emitted after the per-operation decision is known, for
successful and denied attempts alike. [*check.auditing.continuous-both-outcomes] The subject and process recorded
are the **operation-time** effective token and current task, not
necessarily the ones that opened the handle. [*check.auditing.continuous-operation-time-subject] That keeps attribution
correct after a handle is passed between processes, while still using
the opener-computed mask to decide whether the handle is audited at
all.

An enforcement point that cannot construct a required continuous-audit
event fails closed. [*check.auditing.continuous-fails-closed] Transport buffering and drop accounting remain
KMES's concern (§2.7).

## Privilege-use auditing

When a privilege is exercised to grant access the DACL would not have
granted independently, a privilege-use event may be emitted. This runs
after the complete pipeline — after integrity policy, confinement and
central access policy — so it reflects the final result rather than an
intermediate one. [*check.auditing.privilege-use-after-pipeline]

**Successful** privilege use means the privilege's contributed bits
survive into the final granted result. The privilege is marked used,
and an event is emitted when the token's `audit_policy` carries
`PRIVILEGE_USE_SUCCESS` (0x04). [*check.auditing.privilege-use-success] **Failed** privilege use means the
privilege contributed bits during evaluation that did not survive. The
privilege is *not* marked used, and an event is emitted under
`PRIVILEGE_USE_FAILURE` (0x08). [*check.auditing.privilege-use-failure] A privilege that contributed nothing
to the requested access produces no event either way. [*check.auditing.privilege-use-no-contribution]

With an object type list, the test is per-node: a privilege counts as
successfully used if its bits survive on *any* node's final mask. [*check.auditing.privilege-use-per-node]

A `MAXIMUM_ALLOWED` request short-circuits this stage entirely,
recording no used bits and emitting no privilege-use events at all. [*check.auditing.max-allowed-skips-privilege-use]

How counterfactual the accounting really is varies by privilege, as
§3.4.1 describes: `SeSecurityPrivilege` and `SeTakeOwnershipPrivilege`
contribute only where the DACL had not already granted the right,
while backup and restore seed their bits unconditionally and so also
report use for accesses the DACL alone would have permitted. [*check.auditing.backup-restore-overreport]

## Per-token audit policy

A token's `audit_policy` can force events regardless of SACL content.
This runs after the SACL walk and before result computation: if the
access succeeded and the policy carries `OBJECT_ACCESS_SUCCESS`
(0x01), a success event is emitted; if it failed and the policy
carries `OBJECT_ACCESS_FAILURE` (0x02), a failure event is. [*check.auditing.forced-events]

Success here means every requested bit was granted, or that nothing
was requested at all. [*check.auditing.forced-success-definition]

These events are additive — they fire even when no SACL ACE matched —
and they carry the `object_audit_context` the caller supplied. [*check.auditing.forced-additive] The
policy is per-token, fixed at creation, and follows impersonation,
since it is read from the effective token. [*check.auditing.policy-from-effective-token]

## Event contents

An event carries the **subject**, the calling token's identity — user
SID, group SIDs, integrity level, PIP identity; the **object**, as the
caller-provided context; the **access**, meaning what was requested,
what was granted, and whether the request succeeded; the **trigger**,
which audit ACE matched or which privilege was exercised; and the
**process**, its PID, name and executable path. [*check.auditing.event-contents]

The pipeline itself produces only the object-and-access half — the
matched ACE bytes, the requested and granted masks, the outcome,
whether the event was policy-forced, the privilege, and the audit
context. The subject and process halves are attached at emission time
from the resolved call context, which is also where the effective PIP
values used for the verdict are reused for attribution.

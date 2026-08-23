---
title: Auditing in AccessCheck
description: Auditing is purely observational and never changes a decision — access, continuous and privilege-use auditing, and per-token policy.
---

Auditing is purely observational. No audit rule affects the access
decision, and audit ACEs are evaluated after the decision is final.

Three mechanisms operate inside the pipeline, emitting two families of
KMES record: `access-audit` for object-access events from the SACL
walk and from token audit-policy forcing, and `privilege-use` for
privilege-use events. A third family, `caap-policy-diagnostic`, is
emitted for the CAAP conditions of §3.8.8 — a SACL evaluation error,
or a staged-versus-effective mismatch. The event type strings and
payload schemas are in §3.C.

Event delivery happens before any result is written back to the
caller, and a failure to deliver fails the call. An audit event cannot
be suppressed by handing the syscall a bad output pointer.

## Access auditing

`SYSTEM_AUDIT` ACEs in the SACL define which attempts to log. Each
carries a SID, an access mask, and success and failure flags —
`SUCCESSFUL_ACCESS_ACE_FLAG` (0x40) and `FAILED_ACCESS_ACE_FLAG`
(0x80).

An event is emitted when the ACE's SID matches the caller, its mask
overlaps the requested access, and its flags match the outcome.

Two details matter. The SID is matched with **deny polarity** — the
broadest identity view, in which deny-only groups are visible —
because auditing should capture the widest possible picture rather
than the narrowest. And the overlap is tested against the
generic-mapped **requested** mask, not the final granted mask, so a
failed request is still auditable for the rights it actually asked
for.

Conditional audit ACEs gate the event on an expression, using the same
deny-side membership polarity. An expression evaluating to UNKNOWN
emits the event: when in doubt, audit.

## Continuous auditing

Access auditing fires once, where AccessCheck runs. Continuous
auditing covers per-operation monitoring.

`SYSTEM_ALARM` ACEs configure it. When AccessCheck evaluates an alarm
ACE whose SID matches, the ACE's mask is accumulated into a
**continuous audit mask** returned to the caller, which stores it on
the open handle and enforces it per operation. Conditional alarm ACEs
use the same deny-side polarity as conditional audit ACEs. The alarm
branch deliberately performs no overlap test against the requested
mask — an alarm ACE contributes its mask on a SID match alone.

On each later operation the enforcement point emits a
`continuous-audit` event when the operation's normalised
required-access mask overlaps the stored mask. For FACS handles that
is the same mask used by the use-time check (§3.9.4). Where an
operation's authorization accepts any one of several rights — append
or write data, say — the required mask holds the accepted set and the
event records the subset that overlapped.

Events are emitted after the per-operation decision is known, for
successful and denied attempts alike. The subject and process recorded
are the **operation-time** effective token and current task, not
necessarily the ones that opened the handle. That keeps attribution
correct after a handle is passed between processes, while still using
the opener-computed mask to decide whether the handle is audited at
all.

An enforcement point that cannot construct a required continuous-audit
event fails closed. Transport buffering and drop accounting remain
KMES's concern (§2.7).

## Privilege-use auditing

When a privilege is exercised to grant access the DACL would not have
granted independently, a privilege-use event may be emitted. This runs
after the complete pipeline — after integrity policy, confinement and
central access policy — so it reflects the final result rather than an
intermediate one.

**Successful** privilege use means the privilege's contributed bits
survive into the final granted result. The privilege is marked used,
and an event is emitted when the token's `audit_policy` carries
`PRIVILEGE_USE_SUCCESS` (0x04). **Failed** privilege use means the
privilege contributed bits during evaluation that did not survive. The
privilege is *not* marked used, and an event is emitted under
`PRIVILEGE_USE_FAILURE` (0x08). A privilege that contributed nothing
to the requested access produces no event either way.

With an object type list, the test is per-node: a privilege counts as
successfully used if its bits survive on *any* node's final mask.

A `MAXIMUM_ALLOWED` request short-circuits this stage entirely,
recording no used bits and emitting no privilege-use events at all.

How counterfactual the accounting really is varies by privilege, as
§3.4.1 describes: `SeSecurityPrivilege` and `SeTakeOwnershipPrivilege`
contribute only where the DACL had not already granted the right,
while backup and restore seed their bits unconditionally and so also
report use for accesses the DACL alone would have permitted.

## Per-token audit policy

A token's `audit_policy` can force events regardless of SACL content.
This runs after the SACL walk and before result computation: if the
access succeeded and the policy carries `OBJECT_ACCESS_SUCCESS`
(0x01), a success event is emitted; if it failed and the policy
carries `OBJECT_ACCESS_FAILURE` (0x02), a failure event is.

Success here means every requested bit was granted, or that nothing
was requested at all.

These events are additive — they fire even when no SACL ACE matched —
and they carry the `object_audit_context` the caller supplied. The
policy is per-token, fixed at creation, and follows impersonation,
since it is read from the effective token.

## Event contents

An event carries the **subject**, the calling token's identity — user
SID, group SIDs, integrity level, PIP identity; the **object**, as the
caller-provided context; the **access**, meaning what was requested,
what was granted, and whether the request succeeded; the **trigger**,
which audit ACE matched or which privilege was exercised; and the
**process**, its PID, name and executable path.

The pipeline itself produces only the object-and-access half — the
matched ACE bytes, the requested and granted masks, the outcome,
whether the event was policy-forced, the privilege, and the audit
context. The subject and process halves are attached at emission time
from the resolved call context, which is also where the effective PIP
values used for the verdict are reused for attribution.

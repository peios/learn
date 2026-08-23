---
title: caap-policy-diagnostic
description: Two unrelated central-access-policy conditions sharing one event type, told apart by the kind field — and the limits of the mismatch report.
---

Fires during the central access policy step of AccessCheck, for two
unrelated conditions distinguished by the `kind` field: a CAAP SACL that
failed to evaluate, and a staged policy that would have decided
differently from the effective one.

Event type string: `caap-policy-diagnostic`.

| Key | Type | Meaning |
|---|---|---|
| `subject` | map | Subject record (§2.1). |
| `object_context` | bin or nil | Caller-supplied object identifier. |
| `kind` | string | `sacl-error` or `staging-mismatch`. |
| `phase` | string | Which phase of CAAP evaluation produced the diagnostic. |
| `policy_sid` | bin or nil | The policy involved. `nil` for `staging-mismatch`. |
| `rule_index` | uint or nil | The rule involved. `nil` for `staging-mismatch`. |
| `reason` | string or nil | Diagnostic text, for `sacl-error`. |
| `requested_access` | uint | The mask the caller requested. |
| `effective_granted_access` | uint | Total granted under the effective policy. |
| `staged_granted_access` | uint | Total the staged policy would have granted. |
| `object_results_differ` | bool | Whether staged and effective differed for this object. |
| `process` | map | Process record (§2.2). |

Every key is always present; several are `nil` depending on `kind`.

## kind = sacl-error

A central access rule's SACL could not be evaluated. `policy_sid`,
`rule_index` and `reason` identify what failed and where.

This is a defect in the policy, not in the access. The access is still
decided; the event says a rule that should have participated could not.

## kind = staging-mismatch

A staged policy — one being trialled before it takes effect — would have
produced a different result from the policy actually in force. This is
the mechanism's whole purpose: run the new policy in parallel and report
where it would have changed something, before it can break anything.

`policy_sid` and `rule_index` are `nil` here. The mismatch is a property
of the whole evaluation, not attributable to one rule.

## The limits of the mismatch report

Worth knowing before building anything on it.

It carries the two total granted masks and a boolean. It does **not**
identify which rule differed, and it does not report which audit events
would have changed.

For a mismatch that is purely in SACL behaviour, the two masks can be
**equal** while `object_results_differ` is true. A consumer comparing
only the masks will conclude nothing changed.

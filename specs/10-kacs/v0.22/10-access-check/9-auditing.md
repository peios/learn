---
title: Auditing in AccessCheck
---

Auditing is purely observational. No audit rule affects the access decision. Audit ACEs are evaluated after the access decision is final.

KACS defines three auditing mechanisms within the AccessCheck pipeline.

## Access auditing

SYSTEM_AUDIT ACEs in the SACL define which access attempts to log. Each audit ACE specifies:

- **A SID** — matched using deny polarity (the broadest identity view -- deny-only groups are visible). Auditing SHOULD capture the widest possible picture.
- **An access mask** — which operations are audited.
- **Success and/or failure flags** — SUCCESSFUL_ACCESS_ACE_FLAG (0x40) and FAILED_ACCESS_ACE_FLAG (0x80) control whether to audit successful access, failed access, or both.

When an audit ACE's SID matches the caller, its mask overlaps with the
generic-mapped requested access mask, and its success/failure flags match the
final outcome, an audit event is emitted.

The overlap check uses the mapped requested mask after generic mapping
(`mapped_desired` in the algorithm), not the final granted mask. This ensures
failed requests are still auditable for the rights that were actually
requested.

Conditional audit ACEs carry expressions that gate whether the event fires. An expression that evaluates to UNKNOWN results in the event being emitted (when in doubt, audit).

## Continuous auditing

Access auditing fires once, at the point where AccessCheck runs. Continuous auditing fills the gap for per-operation monitoring.

SYSTEM_ALARM ACEs configure per-operation audit masks. When AccessCheck evaluates an alarm ACE and the caller's SID matches, the ACE's access mask is recorded as a **continuous audit mask** on the open handle. On each subsequent operation, the enforcement point checks the handle's continuous audit mask and emits an event if the operation matches.

The continuous audit mask is returned by AccessCheck to the caller (FACS, registryd), which stores it on the handle and enforces it per-operation.

## Privilege-use auditing

When a privilege is exercised to grant access that the DACL would not have independently granted, a privilege-use audit event MAY be emitted. This fires after the complete evaluation pipeline -- after integrity policy, confinement, and central access policy.

KACS distinguishes success and failure privilege-use auditing:

- **Successful privilege use** — the privilege contributed requested bits that survive to the final granted result. In this case the privilege is marked used, and a privilege-use audit event is emitted when `audit_policy & PRIVILEGE_USE_SUCCESS` (0x04).
- **Failed privilege use** — the privilege contributed requested bits during evaluation, but those bits do not survive to the final granted result. In this case the privilege is not marked used, and a privilege-use audit event is emitted when `audit_policy & PRIVILEGE_USE_FAILURE` (0x08).

If a privilege did not contribute to the requested access at all, no privilege-use audit event is emitted.

## Per-token audit policy (algorithm step 15b)

The token's `audit_policy` field MAY force audit events for specific categories regardless of SACL content. This runs after the SACL walk (step 15) and before result computation (step 16). The kernel checks:

- If the access succeeded and `audit_policy & OBJECT_ACCESS_SUCCESS` (0x01): emit a success audit event.
- If the access failed and `audit_policy & OBJECT_ACCESS_FAILURE` (0x02): emit a failure audit event.

These events are additive — they fire even if no SACL ACE matched. The `object_audit_context` from the AccessCheck caller is included in the event. Token audit policy is per-token, set at creation time, and follows impersonation (the impersonated token's policy applies during impersonation).

## Audit event contents

Each audit event contains:

- **Subject** — the calling token's identity (user SID, group SIDs, integrity level, PIP identity) and `auth_id` (logon session LUID, for correlating events to logon sessions).
- **Object** — caller-provided context identifying the object.
- **Access** — what was requested, what was granted, whether the request succeeded or failed.
- **Trigger** — which audit ACE matched, or which privilege was exercised.
- **Process** — the calling process's PID, name, and executable path.

> [!INFORMATIVE]
> The event format and transport mechanism (kernel ring buffer to userspace eventd) are specified in the Peios Observability Specification (KMES), not in this document.

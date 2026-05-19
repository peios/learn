---
title: Audit ACEs
type: concept
description: Audit ACEs in an object's SACL fire events when matching access occurs. SYSTEM_AUDIT ACEs fire once per access, at handle creation. SYSTEM_ALARM ACEs configure per-operation audit on the open handle. This page covers both types, the conditional variants, the audit polarity rule for SID matching, and the UNKNOWN-fires-the-event rule.
related:
  - peios/auditing/overview
  - peios/auditing/policy-forced-auditing
  - peios/auditing/events-and-transport
  - peios/security-descriptors/the-sacl
  - peios/security-descriptors/conditional-aces
---

The primary mechanism for object-access auditing is **audit ACEs** in an object's SACL. An audit ACE says: when a specific principal (or principals matching a SID) attempts specific access rights, fire an event. The ACE can be conditioned on whether the attempt succeeded, whether it failed, or both. The event records the access; the access itself is decided by the DACL and the rest of the pipeline.

This page covers the two audit ACE families — `SYSTEM_AUDIT*` (one-shot at handle creation) and `SYSTEM_ALARM*` (continuous per-operation) — and the rules that govern when each fires.

## SYSTEM_AUDIT — one event per access

A `SYSTEM_AUDIT` ACE fires once when an access check completes. The ACE has the standard single-SID structure:

| Field | Meaning |
|---|---|
| AceType | `SYSTEM_AUDIT` (0x02), or one of the object/callback variants (0x07, 0x0D, 0x0F) |
| AceFlags | Includes `SUCCESSFUL_ACCESS_ACE_FLAG` (0x40) and/or `FAILED_ACCESS_ACE_FLAG` (0x80) |
| Mask | The access mask the ACE is interested in |
| SID | The principal the ACE targets |

When an access check is in step 14 (the SACL audit walk), the kernel scans the SACL for audit ACEs. For each `SYSTEM_AUDIT` ACE, it asks:

1. Does the caller's identity match the ACE's SID? If not, the ACE does not apply.
2. Does the requested access overlap the ACE's mask? If not, the ACE does not apply.
3. If the access succeeded and the ACE has `SUCCESSFUL_ACCESS_ACE_FLAG` set, emit an event.
4. If the access failed and the ACE has `FAILED_ACCESS_ACE_FLAG` set, emit an event.
5. Otherwise the ACE applies but does not fire.

One event per matching ACE. An object with three matching audit ACEs produces three events on a single access. A separate access later — a new handle, a new access check — produces a separate set of events.

The event is for the *access check* as a whole. It does not fire per-operation on the open handle; once the handle is open, subsequent operations do not re-fire the audit ACE. (For per-operation audit, see `SYSTEM_ALARM` below.)

### Common patterns

The `SUCCESSFUL_ACCESS_ACE_FLAG` and `FAILED_ACCESS_ACE_FLAG` flags can both be set in one ACE:

| Flag combination | Audit behaviour |
|---|---|
| `SUCCESSFUL_ACCESS_ACE_FLAG` only | Audit only when the access succeeded. |
| `FAILED_ACCESS_ACE_FLAG` only | Audit only when the access was denied. |
| Both set | Audit every access attempt, regardless of outcome. |
| Neither set | The ACE applies but never fires. |

The "both set" pattern is what you reach for when you want a complete audit log for an object — every attempt, allowed or denied. The "failed only" pattern is useful for security monitoring: alert me whenever someone tries to do X but is refused. The "successful only" pattern is useful for compliance: record everyone who has actually touched this thing.

A SACL with no audit ACEs produces no audit events (unless `audit_policy` on the token fires; see [Policy-forced auditing](~peios/auditing/policy-forced-auditing)). A SACL with audit ACEs but no relevant flags set is auditing nothing — the ACEs are essentially comments at that point. The flags are what makes them active.

## SYSTEM_ALARM — continuous, per-operation

A `SYSTEM_ALARM` ACE works differently. It does not fire at access-check time; instead, it configures a **continuous audit mask** on the open handle, and every subsequent operation through the handle whose required access overlaps that mask produces an event.

The ACE has the same structure as `SYSTEM_AUDIT`:

| Field | Meaning |
|---|---|
| AceType | `SYSTEM_ALARM` (0x03), or one of the variants (0x08, 0x0E, 0x10) |
| AceFlags | Same flag bits as audit |
| Mask | The mask to record on the handle |
| SID | The targeted principal |

During step 14 of access check, when a `SYSTEM_ALARM` ACE matches, the kernel:

1. Computes a continuous-audit mask — the union of all matching alarm ACEs' masks.
2. Returns the mask to the caller as part of the access check's output.
3. The caller (typically FACS for files, or registryd for registry keys) stores the mask on the open handle.

Then, on each subsequent operation through the handle, the enforcement point compares the operation's required-access mask against the handle's continuous audit mask. If they overlap (any bit shared), the kernel emits a `continuous-audit` event for the operation.

### Audit vs alarm: granularity

The difference between `SYSTEM_AUDIT` and `SYSTEM_ALARM` is fundamentally about granularity:

| Aspect | `SYSTEM_AUDIT` | `SYSTEM_ALARM` |
|---|---|---|
| Event timing | Once, at access-check completion | Per operation on the open handle |
| Event count per handle | One (or one per matching ACE) | Many — one per matching operation |
| What is recorded | The access-check decision | The specific operation that was performed |
| Storage of state | None — fires and forgets | Continuous audit mask on the handle |
| Use case | "Who opened this file with these rights" | "Every read this principal performed on this object" |

For most auditing, `SYSTEM_AUDIT` is the right tool. The event volume is bounded by the number of distinct accesses, which is usually small.

For high-sensitivity objects where every operation matters — auditing a credential store's every read, recording every write to a security-relevant log file — `SYSTEM_ALARM` is the right tool. The event volume is bounded by operation count, which can be high, but the visibility into what is actually being done is also higher.

Both can coexist on the same SACL. A SACL with both `SYSTEM_AUDIT` and `SYSTEM_ALARM` produces an at-open event from the audit ACE and per-operation events from the alarm ACE.

## Audit polarity for SID matching

A subtle but important rule: audit ACEs match SIDs with **deny polarity** rather than allow polarity.

For an `ACCESS_ALLOWED` ACE in a DACL, a group on the token matches only if it has `SE_GROUP_ENABLED` set. Groups marked `SE_GROUP_USE_FOR_DENY_ONLY` are invisible to allow ACEs.

For an `ACCESS_DENIED` ACE, both regular groups and deny-only groups match. The broader view exists so denies cannot be sidestepped by demoting a group to deny-only.

**Audit ACEs use the same broad view as deny ACEs.** A token's deny-only groups match audit ACEs. Logon SIDs, disabled groups in some cases, every SID associated with the token contributes to audit matching.

The reasoning: the purpose of auditing is to capture the most complete picture of the identity making the access. A token that has been restricted (groups marked deny-only, say) is still that token, with that identity, and the audit log should reflect that. Limiting audit to the narrower allow-polarity view would let auditing miss accesses by tokens that had been deliberately downgraded.

Practical effect: if you write an audit ACE matching a specific group SID, it will fire whether the calling token currently has that group enabled, disabled, or marked deny-only. The audit ACE catches the broadest possible identity match.

## Conditional audit ACEs

The callback variants of audit and alarm ACEs (`SYSTEM_AUDIT_CALLBACK`, `SYSTEM_AUDIT_CALLBACK_OBJECT`, `SYSTEM_ALARM_CALLBACK`, `SYSTEM_ALARM_CALLBACK_OBJECT`) add a conditional expression. The ACE fires only when the expression evaluates appropriately for an audit.

The rule: an audit-callback ACE fires when its expression evaluates to **TRUE or UNKNOWN**. It does not fire on FALSE.

This is the **opposite** of the rule for `ACCESS_ALLOWED_CALLBACK` (where TRUE fires the allow, UNKNOWN does not) and matches the rule for `ACCESS_DENIED_CALLBACK` (TRUE or UNKNOWN fires the deny).

The reasoning: an audit ACE's job is to record events. Erring on the side of recording — including when the conditional cannot be definitively evaluated — produces a more complete audit log. A missed event is more dangerous than an extra one. UNKNOWN, therefore, fires the audit.

Practical pattern: an audit ACE conditioned on "the request came from outside the trusted network" — `@Local.Source != "internal"` — fires on accesses where the local-claims do not include a `Source` value (the expression evaluates UNKNOWN). The audit log captures the access even though the condition could not be evaluated; an investigator reviewing the log can decide whether the missing claim is meaningful.

## Object-scoped audit ACEs

The object variants (`SYSTEM_AUDIT_OBJECT`, etc.) carry one or two GUIDs that scope the ACE to specific properties of a directory-style object. The audit fires only when the access is to a property whose GUID matches.

For most objects (files, registry keys, processes), object ACEs are not used and the basic single-SID variants are what appears in SACLs. Object ACEs come up in directory-style objects where per-property audit is meaningful — auditing "who read the `manager` property of this user object" rather than just "who read this user object".

The mechanics of object ACEs are the same as elsewhere — the GUID-scoped match — and are covered in [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces). The audit case is identical to the access-check case structurally; only the firing semantics differ.

## Inherit-only audit ACEs

An audit or alarm ACE with `INHERIT_ONLY_ACE` set does not fire on the object it sits on. It is for inheritance to children only — when a child is created, the audit ACE is copied to the child's SACL (subject to inheritance flags) and from then on fires on the child.

This is the same inheritance semantics that DACL ACEs use. An inherit-only audit ACE on a parent directory does not audit accesses to the parent; it just propagates to child files.

## What audit ACEs do not produce

A few clarifications:

- **They do not produce events for accesses that pre-decided.** If MIC or PIP pre-decided write bits as denied at step 5, and the access check ends with the write denied, the audit walk still runs and audit ACEs fire normally. The pre-decision does not skip the audit walk.
- **They do not produce duplicate events on the same handle for the same access.** An access check produces one event per matching ACE. If a process accesses the same object twice (two separate opens, two access checks), each access check produces its own set of events.
- **They do not record per-operation activity on an open handle.** For per-operation events, alarm ACEs are the mechanism. Standard audit ACEs are "at the moment of opening, was this access allowed?".
- **They do not affect access.** The audit walk is observational. A matching audit ACE does not change what gets granted, even if the audit ACE has a different mask than the matching DACL ACE.

## CAAP effective SACLs

A `SYSTEM_SCOPED_POLICY_ID_ACE` in the object's SACL references a central access policy. That policy can have its own effective SACL containing audit ACEs (see [Central access policies](~peios/central-access-policies/overview)). The policy's audit ACEs are collected during CAAP evaluation at step 12 and merged into the audit walk at step 14.

From the audit consumer's perspective, an event triggered by a CAAP's effective SACL looks the same as one triggered by the object's own SACL. The event records what fired, and where the matched ACE came from is part of the event metadata, but the structure is uniform.

Practical implication: a policy administrator who wants to audit a class of objects can put the audit ACE in the policy's effective SACL once, and every object referencing the policy contributes audit events. Better than putting a copy of the audit ACE on every object's SACL individually.

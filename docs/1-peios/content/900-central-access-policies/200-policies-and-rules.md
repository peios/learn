---
title: Policies and rules
type: concept
description: A central access policy is a versioned bundle of rules. Each rule has an optional applies-to expression deciding when it fires, an effective DACL and SACL it contributes to the access check, and optional staged versions for testing. This page covers the structure.
related:
  - peios/central-access-policies/overview
  - peios/central-access-policies/evaluation
  - peios/central-access-policies/staged-policies
  - peios/security-descriptors/conditional-aces
  - peios/security-descriptors/resource-attributes
---

A central access policy is a structured bundle: a version byte, a count of rules, and the rules themselves. Each rule is independently scoped — its applies-to expression decides whether this rule fires on this object — and contributes its own access restriction and audit rules. A policy with three rules can apply to one object via one rule, to another object via two rules, and to a third object via none, depending on the objects' resource attributes.

This page walks through the structure: what a policy contains, what a rule contains, and how the parts fit together. The mechanics of how the policy is actually evaluated during AccessCheck live in [Evaluation](~peios/central-access-policies/evaluation).

## A policy in shape

A policy in its on-wire form is a versioned binary blob:

| Field | Meaning |
|---|---|
| Version | A single byte. v0.20 uses `0x01`. Any other value is rejected at ingestion. |
| Rule count | A 32-bit little-endian count of the rules that follow. Bounded to 256 rules per policy. |
| Rules | Length-prefixed sequence — one entry per rule. |

A policy is not a thing the kernel walks through ACE by ACE. It is a list of rules, each evaluated as its own unit. Two rules in the same policy do not influence each other; either both apply (their applies-to expressions both evaluate TRUE) or one applies or neither.

The kernel holds the parsed policy in its policy cache, keyed by the policy's SID (the SID is established at the time the policy is pushed via `kacs_set_caap` — see [Distribution and recovery](~peios/central-access-policies/distribution-and-recovery)).

## A rule in shape

Each rule is a small structured record:

| Field | Meaning |
|---|---|
| `applies_to` | Optional. A length-prefixed conditional expression in the same bytecode used by callback ACEs. If present, the expression must evaluate TRUE for this rule to apply to a given object; if absent, the rule applies to every object that references the policy. |
| `effective_dacl` | A length-prefixed binary DACL. Required (a rule with no DACL would do nothing). Maximum 65,535 bytes. |
| `effective_sacl` | Optional. A length-prefixed binary SACL contributing audit and policy ACEs. |
| `staged_dacl` | Optional. A proposed replacement for `effective_dacl`, evaluated in parallel for testing. |
| `staged_sacl` | Optional. Same idea for `effective_sacl`. |

Length-prefixed means each part starts with a 32-bit count of bytes followed by that many bytes. An absent field has length zero. The wire-format details are in the [Wire formats reference](~peios/wire-formats-reference/overview); for this page, what matters is the structure.

A rule with no applies-to expression and only an `effective_dacl` is the most common shape. It says "apply this DACL to every object that references this policy".

## The applies-to expression

The `applies_to` expression is a conditional-ACE bytecode expression — the same model as conditional ACEs in DACLs and SACLs (see [Conditional ACEs](~peios/security-descriptors/conditional-aces)). The expression has access to four namespaces:

- `@User.<name>` — claims on the calling token.
- `@Device.<name>` — claims on the calling token's machine identity.
- `@Resource.<name>` — resource attributes on the object being accessed.
- `@Local.<name>` — per-call attributes the caller supplied.

The expression evaluates to TRUE, FALSE, or UNKNOWN. The CAAP rule:

| Result | Effect on the rule |
|---|---|
| TRUE | The rule applies. The effective DACL is evaluated. |
| FALSE | The rule is skipped. |
| UNKNOWN | The rule is **skipped**. |

The UNKNOWN behaviour is **opposite** to the conditional-ACE deny rule. In a DACL, an UNKNOWN expression on a deny ACE causes the deny to apply (fail-closed on deny). For a CAAP applies-to, UNKNOWN causes the *rule* to be skipped (fail-open on the rule's existence). The reason: a rule that does not apply means the running grant is not further restricted; skipping is the conservative choice for CAAP, because the absence of a restriction is the safe default.

This split is worth remembering. The rule of thumb: UNKNOWN always errs in whichever direction does not narrow access. In DACLs, that means UNKNOWN denies are denials (because denying is the existing direction the ACE is going); in CAAP applies-to, that means UNKNOWN rules are skipped (because applying the rule would further narrow access).

Common applies-to expressions:

| Example expression | What it does |
|---|---|
| (absent) | Rule applies to every object that references the policy. |
| `@Resource.Classification == "TopSecret"` | Rule applies only to objects whose Classification resource attribute is TopSecret. |
| `@Resource.Department == "Engineering" && @Resource.Sensitivity == "Internal"` | Rule applies only when both attributes match. |
| `Exists(@Resource.RetentionUntil) && @Resource.RetentionUntil > @Local.Now` | Rule applies only to objects whose retention period has not expired. |

The expression can reference any combination of the four namespaces. It produces a single boolean; whatever combination of attributes you need to inspect, the expression is the place to do it.

## The effective DACL

The `effective_dacl` is a regular DACL — an ACL of ACEs, with the same format any other DACL uses (see [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces)). It is evaluated via a recursive sub-AccessCheck at policy-evaluation time, producing a granted mask for the calling token.

The mask is then intersected with the running grant from the rest of the pipeline. The intersection is the narrowing: bits granted by the rule's effective DACL are preserved; bits not granted are dropped.

The rule's effective DACL can contain any ACE types a regular DACL can. Conditional ACEs work — referencing claims, attributes, and local context. Object ACEs work — scoping by property GUID. Generic rights work — mapped via the object type's GenericMapping table at evaluation time, exactly as they would be in a regular DACL.

What the effective DACL cannot do: include `SYSTEM_SCOPED_POLICY_ID_ACE` references to other policies. Even if such ACEs were present, the kernel's no-recursion rule strips them before evaluating the synthetic SD (see [Evaluation](~peios/central-access-policies/evaluation)). CAAP rules do not nest.

The maximum size of an effective DACL is 65,535 bytes — the same limit a regular DACL has.

## The effective SACL

The `effective_sacl` is optional. When present, it contributes its ACEs to the access check's SACL walk for the object being evaluated. This lets a policy contribute audit rules that fire alongside the object's own audit ACEs.

The audit ACEs in an effective SACL fire based on the final access decision, not on the policy's contribution to it. An audit ACE in an effective SACL that matches a successful access fires as a "successful access" event, regardless of whether the success came from the object's own DACL or from any specific policy.

This is the audit half of CAAP. A policy that wants to log every access to objects it covers — for regulatory or compliance reasons — does so by including an audit ACE in its effective SACL. The audit ACE applies wherever the rule applies, without the object's own administrator needing to add an audit ACE on every object.

The effective SACL can also contain `SYSTEM_MANDATORY_LABEL`, `SYSTEM_PROCESS_TRUST_LABEL`, and `SYSTEM_RESOURCE_ATTRIBUTE` ACEs — but they are not respected at policy evaluation. CAAP can only contribute to **audit**. It cannot apply a mandatory label or PIP label to an object through this channel. Those entries, if present, are ignored.

## Staged DACL and SACL

The `staged_dacl` and `staged_sacl` fields hold proposed replacements for the corresponding effective entries. They are evaluated in parallel during AccessCheck but do not affect the granted mask. Their purpose is to let administrators test policy changes against real traffic without committing.

If the staged DACL would have produced a different granted mask, or the staged SACL would have produced a different set of audit events, the access check sets a **staging mismatch flag** in its output. Tools watching for mismatches can use the flag to discover where a proposed policy change would have changed behaviour.

The full mechanics — when staging is used, what the mismatch flag actually contains, how rollout proceeds — are in [Staged policies](~peios/central-access-policies/staged-policies).

## A complete rule, in shape

Putting it all together, a CAAP rule for "TopSecret objects can only be read by users in the Cleared group" might look like:

| Field | Value |
|---|---|
| `applies_to` | `@Resource.Classification == "TopSecret"` |
| `effective_dacl` | An ACL containing: `ACCESS_ALLOWED Cleared-Group GENERIC_READ`, and nothing else. |
| `effective_sacl` | An ACL containing: `SYSTEM_AUDIT_ACE Everyone GENERIC_READ` with `SUCCESSFUL_ACCESS_ACE_FLAG | FAILED_ACCESS_ACE_FLAG` — log every attempt to access a TopSecret object. |
| `staged_dacl` | (absent) |
| `staged_sacl` | (absent) |

A user not in the Cleared group attempting to read a TopSecret object: the rule applies (attribute matches), the effective DACL grants `GENERIC_READ` only to the Cleared group, the user is not in the group so the rule grants nothing, the intersection drops `GENERIC_READ` from the running grant. Access denied. The audit ACE in the effective SACL records the attempt.

A user in the Cleared group attempting to read the same object: the rule applies, the DACL grants `GENERIC_READ` to the Cleared group, the user is in the group, the rule contributes `GENERIC_READ` to the intersection, the running grant survives, access succeeds. The audit ACE still records the access.

A user (anyone) attempting to read an object whose Classification is "Internal", not "TopSecret": the rule's applies-to evaluates FALSE, the rule is skipped, the running grant passes through unchanged. CAAP contributes nothing on this access.

## Limits

For reference, the size and count limits the kernel enforces at ingestion:

| Limit | Value |
|---|---|
| Wire-format spec size | 256 KB |
| Rules per policy | 256 |
| Bytes per applies-to expression | 64 KB |
| Bytes per effective or staged DACL/SACL | 65,535 (matches the SD format limit) |
| Version byte | Must be `0x01` |

A policy exceeding any of these is rejected by `kacs_set_caap` with `-EINVAL`. The limits are generous; a realistic policy will be far below them.

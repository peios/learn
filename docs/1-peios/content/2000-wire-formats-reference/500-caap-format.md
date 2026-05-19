---
title: CAAP format
type: reference
description: The byte-level format for central access policies passed to kacs_set_caap. A versioned bundle of rules, each with an applies-to expression, an effective DACL/SACL, and optional staged variants for testing. This page covers the layout, the rule structure, and the size limits.
related:
  - peios/wire-formats-reference/overview
  - peios/wire-formats-reference/security-descriptors
  - peios/wire-formats-reference/conditional-ace-bytecode
  - peios/central-access-policies/overview
  - peios/central-access-policies/policies-and-rules
---

A central access policy in wire form is a versioned record containing zero or more rules. Each rule has an optional applies-to expression, an effective DACL, and optional effective SACL plus staged variants. The kernel reads this format when authd (or peinit, in early boot) pushes a policy via `kacs_set_caap`.

This page is the byte-level reference. The conceptual model — what CAAP does, how rules are evaluated — is in [Central access policies](~peios/central-access-policies/overview).

All multi-byte integers are little-endian.

## Top-level layout

| Bytes | Field | Meaning |
|---|---|---|
| 0 | `version` (u8) | `0x01` in v0.20. Other values rejected. |
| 1–4 | `rule_count` (u32le) | Number of rules following. Max 256. |
| 5+ | rules | `rule_count` rules, packed back-to-back. |

Each rule is self-delimiting (its lengths tell the reader where it ends), so the rules can be walked without an external index.

## Rule layout

Each rule has five length-prefixed sections, all optional except `effective_dacl`:

| Section | Format |
|---|---|
| `applies_to` | `[length:u32le][bytecode bytes]` — length 0 means absent. |
| `effective_dacl` | `[length:u32le][DACL bytes]` — length must be > 0. |
| `effective_sacl` | `[length:u32le][SACL bytes]` — length 0 means absent. |
| `staged_dacl` | `[length:u32le][DACL bytes]` — length 0 means absent. |
| `staged_sacl` | `[length:u32le][SACL bytes]` — length 0 means absent. |

The five sections appear in this order. Each starts with a u32 length; if length is 0, no bytes follow for that section, and the next section begins immediately.

### applies_to

The applies-to expression. Format is conditional ACE bytecode (with the `0x61 0x72 0x74 0x78` magic prefix) as documented in [Conditional ACE bytecode](~peios/wire-formats-reference/conditional-ace-bytecode).

If absent (length 0), the rule applies to every object that references the policy. If present, the rule applies only when the expression evaluates to TRUE for the object being accessed.

The expression can reference any of the four attribute namespaces: `@User.*` (caller's user claims), `@Device.*` (caller's device claims), `@Resource.*` (object's resource attributes), `@Local.*` (caller-supplied local claims).

UNKNOWN result on applies-to causes the **rule to be skipped** (not applied). This is opposite to deny ACE behaviour where UNKNOWN causes the deny to fire; for CAAP applies-to, skipping is the conservative choice (since CAAP only narrows, skipping a rule means *less* narrowing, which is the safe default for "we don't know if this applies").

### effective_dacl

A binary DACL in the standard SD-ACL format (the same format used inside an SD's DACL — see [Security descriptors](~peios/wire-formats-reference/security-descriptors)).

This is **required** — every rule must have an effective_dacl with length > 0. A rule with empty effective_dacl would be meaningless.

The DACL is evaluated against the calling token in a recursive sub-AccessCheck during step 12 of the pipeline. The result is intersected with the running grant.

The DACL can contain any ACE types a regular DACL can — `ACCESS_ALLOWED`, `ACCESS_DENIED`, object ACEs, callback ACEs. The kernel evaluates them the same way it would in a regular DACL walk.

**The DACL cannot contain `SYSTEM_SCOPED_POLICY_ID_ACE` entries** (no nested CAAP references). The kernel does not reject CAAPs that contain such ACEs at ingestion, but it strips them from the synthetic SD during sub-AccessCheck so they have no effect.

### effective_sacl

Optional. A binary SACL containing audit ACEs (and potentially other SACL ACE types).

If present, the audit ACEs in the effective_sacl are added to the audit walk's source set during step 14 of AccessCheck for any object the rule applies to. The audit events fire based on the final access decision, exactly as if the audit ACEs were on the object's own SACL.

The SACL **can** contain:

- `SYSTEM_AUDIT*` ACEs (one-shot audit at access).
- `SYSTEM_ALARM*` ACEs (continuous per-operation audit).

The SACL **should not** contain (kernel ignores if present):

- `SYSTEM_MANDATORY_LABEL_ACE` — CAAPs cannot impose mandatory integrity labels on objects through this channel.
- `SYSTEM_PROCESS_TRUST_LABEL_ACE` — same for PIP.
- `SYSTEM_RESOURCE_ATTRIBUTE_ACE` — CAAPs cannot add resource attributes to objects.
- `SYSTEM_SCOPED_POLICY_ID_ACE` — no nested policy references.

These restrictions reflect the model: CAAP contributes to *audit* policy and *access narrowing*; it doesn't redefine objects' fundamental security state.

### staged_dacl

Optional. A proposed replacement for `effective_dacl`, evaluated in parallel during step 12 without affecting the granted mask.

If the staged_dacl produces a different result than the effective_dacl for the same call, the access check sets the **staging mismatch** flag in its output. Tools watching for mismatches use the flag to learn where a staged policy change would have changed behaviour.

The staged_dacl has the same format and same restrictions as effective_dacl — it's a regular DACL, internally evaluated the same way.

### staged_sacl

Optional. Same idea, for audit policy. If the staged_sacl would have produced different audit events than the effective_sacl, the staging mismatch flag is set.

## Validation

The kernel validates a CAAP spec at ingestion time:

1. **Size**: total spec is at most 256 KB. The version byte plus rule_count plus rules must fit.
2. **Version**: byte 0 must be `0x01`.
3. **Rule count**: at most 256.
4. **Per-rule**:
   - All five length fields must fit within the spec.
   - `effective_dacl` length must be > 0.
   - Each ACL must parse cleanly (header, ACE count, AceSizes, etc.).
   - Each DACL must be at most 65,535 bytes (the SD ACL limit).
   - `applies_to` (if present) must be at most 64 KB.
   - Each conditional expression (applies_to, plus any callback ACE expressions in the DACLs/SACLs) must be structurally valid.
5. **No nested CAAPs**: SYSTEM_SCOPED_POLICY_ID_ACEs in DACLs and SACLs are accepted but stripped during evaluation; the kernel does not reject them at ingestion.

A failure returns `-EINVAL`. The policy is not added to (or replaced in) the cache.

## Limits

| Limit | Value |
|---|---|
| Total spec size | 256 KB |
| Rules per policy | 256 |
| Effective/staged DACL or SACL size | 65,535 bytes (matches SD ACL limit) |
| Applies-to expression bytecode | 64 KB |
| Version byte | `0x01` |

## Encoded example

A simplified CAAP with one rule that applies to TopSecret objects and grants read-only to a Cleared group:

```
[version: 0x01]
[rule_count: 0x01 0x00 0x00 0x00]

Rule 1:
  [applies_to_len: 0x44 0x00 0x00 0x00 (68 bytes — placeholder)]
  [applies_to bytes: 0x61 0x72 0x74 0x78 (artx)
                     ... conditional bytecode for @Resource.Classification == "TopSecret" ...]
  [effective_dacl_len: 0x30 0x00 0x00 0x00 (48 bytes — placeholder)]
  [effective_dacl bytes: ACL header + ACCESS_ALLOWED ACE for Cleared group + GENERIC_READ]
  [effective_sacl_len: 0x00 0x00 0x00 0x00 (none)]
  [staged_dacl_len: 0x00 0x00 0x00 0x00 (none)]
  [staged_sacl_len: 0x00 0x00 0x00 0x00 (none)]
```

The total spec is small — a few hundred bytes for this minimal example. A real-world policy with multiple rules and richer DACLs is larger but still well within the 256 KB limit.

## Updates and removal

`kacs_set_caap` is the syscall for both creating and updating policies. The arguments include the policy's SID; the kernel uses the SID as the cache key.

- **Create / replace**: pass a non-NULL `spec`. The kernel parses, validates, and replaces (or creates) the cache entry at this SID.
- **Remove**: pass NULL for `spec` (with `spec_len = 0`). The kernel deletes the cache entry at this SID.

Removal is the way to clean up a policy that is no longer referenced. The kernel does not auto-evict; explicit removal is required.

If a policy is removed while objects still reference it (their SACLs still contain `SYSTEM_SCOPED_POLICY_ID_ACE` pointing at the now-removed SID), those references resolve to the **recovery policy** at the next access check on each such object. The recovery policy grants `GENERIC_ALL` to `BUILTIN\Administrators`, `SYSTEM`, and `OWNER_RIGHTS` — see [Distribution and recovery](~peios/central-access-policies/distribution-and-recovery).

## Replacement semantics

A subsequent `kacs_set_caap` for the same SID replaces the existing entry atomically. The replacement:

- The new spec is parsed and validated.
- If validation succeeds, the old entry is replaced with the new one. The transition is atomic from the kernel's perspective; an access check in progress sees either the old or the new entry, never a mixed state.
- The kernel's policy cache generation counter increments (similar to mount policies' generation counter — used to invalidate any cached evaluation state derived from the old policy).
- If validation fails, the old entry is left in place; the call returns `-EINVAL`.

This is the safe-replacement pattern. Updating a policy is one syscall; the kernel handles consistency.

---
title: Central Access and Auditing Policy
---

Central Access and Auditing Policy (CAAP) separates policy definition from the objects it governs. A policy is defined once, centrally. Objects reference the policy by SID via a SYSTEM_SCOPED_POLICY_ID_ACE in their SACL. When the policy changes, every future AccessCheck against a referencing object uses the new rules. Already-open handles are not retroactively affected (check-at-open model).

CAAP extends the Windows Central Access Policy (CAP) model by adding an audit component: each policy rule carries both an access restriction (DACL) and an audit requirement (SACL).

## Policy structure

A CAAP is a named collection of rules, identified by a policy SID. Each rule has:

- **An applies-to condition** (optional) — a conditional expression that determines which objects this rule governs, based on the object's resource attributes. If absent, the rule applies to all objects that reference the policy.

- **An effective DACL** — mandatory access rules enforced by this rule. A real DACL evaluated using the full pipeline.

- **An effective SACL** (optional) — mandatory audit rules enforced by this rule. Audit ACEs in the effective SACL are merged with the object's own SACL during audit evaluation.

- **A staged DACL** (optional) — a proposed replacement for the effective DACL, used for testing.

- **A staged SACL** (optional) — a proposed replacement for the effective SACL, used for testing.

## Access evaluation (DACL component)

The DACL result is an AND with the normal DACL evaluation — CAAP can only further restrict access, never expand it. If the DACL grants read and write but the applicable CAAP rule's effective DACL grants only read, the final result is read.

Multiple SYSTEM_SCOPED_POLICY_ID_ACEs MAY appear in the same SACL, enabling
composable policies. The AND semantics make composition safe — every
additional policy can only further restrict. Inherit-only scoped-policy ACEs
do not apply to the current object and MUST be ignored during CAAP lookup.

> [!INFORMATIVE]
> The reference model allows one scoped policy ACE per SACL. KACS allows multiple.

For each scoped policy ACE, AccessCheck:

1. Looks up the policy in the kernel's policy cache.
2. For each rule whose `applies_to` condition evaluates to TRUE (or has no condition). If `applies_to` evaluates to FALSE or UNKNOWN, the rule is skipped — this is intentionally opposite to the deny-ACE UNKNOWN behavior, because skipping a rule is the conservative choice (the rule's DACL cannot widen access beyond what the normal DACL grants):
   - Evaluates the rule's effective DACL using the full evaluation pipeline (privilege grants, MIC, PIP, DACL walk, restricted tokens, confinement) with one exception: backup/restore intent is not passed (intent is a caller concern, not a policy concern).
   - Intersects the result with the running total (which starts at the normal evaluation's granted mask — CAAP can only reduce, never expand).
3. If no rules apply (all conditions FALSE/UNKNOWN, or policy has no rules), CAAP has no effect — the normal DACL result stands unchanged. CAAP MUST NOT recurse — a CAAP rule's synthetic SD MUST NOT trigger nested CAAP evaluation, even if the original SD's SACL contains additional SYSTEM_SCOPED_POLICY_ID_ACEs.

## Audit evaluation (SACL component)

For each applicable rule that carries an effective SACL, the rule's audit ACEs are evaluated alongside the object's own SACL during the audit walk (step 15 of the AccessCheck algorithm). Audit ACEs from the CAAP effective SACL are treated identically to ACEs from the object's own SACL — if either says "audit this operation," it is audited.

The SACL component is additive: a CAAP SACL can only add audit coverage, never suppress auditing that the object's own SACL requests.

## Policy cache

The kernel maintains a policy cache: a map from policy SID to policy object. The cache is empty at boot.

### Population

Policies are pushed into the kernel cache via the `kacs_set_caap` syscall. Requires SeTcbPrivilege.

| Parameter | Description |
|---|---|
| `policy_sid` | SID identifying the policy. Binary SID format. |
| `policy_sid_len` | Length of the policy SID in bytes. |
| `spec` | Wire-format policy specification. 0 (NULL) = remove the policy. |
| `spec_len` | Length of the spec. 0 = remove the policy. |
| Returns | 0 on success, `-errno` on failure. |

Calling with a non-NULL spec for an existing policy SID replaces the policy. Calling with a NULL spec or zero length removes the policy.

### Wire format

```
[version:u8 = 0x01]
[rule_count:u32le]
per rule:
  [applies_to_len:u32le][applies_to_expr bytes]     (0 = no condition)
  [effective_dacl_len:u32le][effective_dacl bytes]   (binary ACL; MUST NOT be 0)
  [effective_sacl_len:u32le][effective_sacl bytes]   (0 = no audit rules)
  [staged_dacl_len:u32le][staged_dacl bytes]         (0 = no staged DACL)
  [staged_sacl_len:u32le][staged_sacl bytes]         (0 = no staged SACL)
```

Limits:
- Maximum `spec_len`: 256 KB.
- Maximum `rule_count`: 256.
- Maximum individual ACL length: 64 KB (consistent with SD size limit).
- Maximum `applies_to_len`: 64 KB.
- Version byte: MUST be 0x01 for v0.20. Unknown versions are rejected.

All length-prefixed fields use little-endian u32 lengths. ACLs use the standard binary ACL format defined in the Security Descriptor chapter. All ACE types valid for DACLs/SACLs are permitted inside policy ACLs. The applies_to expression is conditional ACE bytecode (same format as CALLBACK ACE application data, including the "artx" prefix).

The `applies_to` expression MUST be structurally valid conditional bytecode at
ingestion time. Malformed or truncated `applies_to` bytecode causes the entire
`kacs_set_caap` call to fail with `-EINVAL`; it MUST NOT be accepted into the
cache and later treated as runtime `UNKNOWN`.

The `effective_dacl_len` MUST NOT be zero — every rule MUST have an effective DACL. A rule with `effective_dacl_len = 0` causes `kacs_set_caap` to return `-EINVAL`.

Parsing errors (truncated fields, lengths exceeding buffer, invalid ACL headers) cause the entire `kacs_set_caap` call to fail with `-EINVAL`. SeTcbPrivilege is checked before any parsing begins.

### Lifecycle

authd is responsible for populating the cache. On a standalone machine, authd reads policies from the registry (loregd). On a domain-joined machine, authd reads policies from Active Directory. The kernel does not know or care about the policy source — it is a passive cache.

authd SHOULD push all policies during early boot, before user-facing services start. If a policy is pushed after services are running, objects already opened with cached access decisions are not retroactively affected (check-at-open model).

## Recovery policy

When a scoped policy ACE references a policy SID not in the kernel cache (authd failed to push, policy was deleted, machine is disconnected), a hardcoded recovery policy is used:

- ALLOW GENERIC_ALL to BUILTIN\Administrators (`S-1-5-32-544`)
- ALLOW GENERIC_ALL to SYSTEM (`S-1-5-18`)
- ALLOW GENERIC_ALL to OWNER_RIGHTS (`S-1-3-4`)

The ACE masks MUST use the literal `GENERIC_ALL` bit (0x10000000), not pre-mapped object-specific bits. `EvaluateSecurityDescriptor` step 3 expands `GENERIC_ALL` via the caller's GenericMapping at evaluation time, ensuring the recovery policy works correctly for all object types.

Because CAAP is applied as an intersection, the recovery policy does not widen access beyond the object's own DACL. It prevents missing CAAP from further restricting access — the object's DACL remains the baseline.

## Error handling

If a CAAP rule's DACL evaluation produces an error (e.g., malformed DACL in the policy definition), the rule denies all access except rights granted by privileges. Privilege-granted rights are preserved as an escape hatch: an administrator with SeSecurityPrivilege retains the ability to read and modify the SACL to remove the scoped policy ACE. Note: PIP enforcement (step 6) runs before CAAP (step 13) and may have already stripped ACCESS_SYSTEM_SECURITY from `privilege_granted` for non-dominant callers. The escape hatch only works for callers who are PIP-dominant or have no PIP trust label on the object.

If a CAAP rule's SACL evaluation produces an error, the error is logged and the rule's audit contribution is skipped.

## Staging

Each CAAP rule MAY carry staged DACLs and SACLs alongside effective ones. AccessCheck evaluates both in parallel. The staged result does not affect access or audit. If the effective and staged results differ, the difference is logged.

Rules without a staged DACL contribute their effective result to both the effective and staged running totals. Rules without a staged SACL contribute their effective SACL to both.

> [!INFORMATIVE]
> Future versions will extend CAAP to support global policies — policies that apply to all objects of a given type (all files, all registry keys) without requiring a per-object SYSTEM_SCOPED_POLICY_ID_ACE. This enables machine-wide audit policies (e.g., "audit all file reads by contractors") defined once rather than stamped on every object.

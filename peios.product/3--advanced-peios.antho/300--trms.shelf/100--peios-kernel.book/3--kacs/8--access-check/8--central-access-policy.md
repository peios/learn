---
title: Central Access and Auditing Policy
description: Policy defined once and referenced by objects — the policy structure, access and audit evaluation, the cache, and the recovery policy.
---

CAAP separates policy definition from the objects it governs. A policy
is defined once, centrally; objects reference it by SID through a
`SYSTEM_SCOPED_POLICY_ID_ACE` in their SACL. When the policy changes,
every future AccessCheck against a referencing object uses the new
rules — already-open handles are unaffected, because the model is
check-at-open.

It extends the Windows Central Access Policy model by adding an audit
component: each rule carries both an access restriction and an audit
requirement.

## Policy structure

A policy is a named collection of rules identified by a policy SID.
Each rule carries:

An optional **applies-to condition**, a conditional expression
determining whether the rule governs this decision. It may reference
the `@Resource`, `@User`, `@Device` and `@Local` claim namespaces, but
it cannot inspect SID or device-group membership: `Member_of`,
`Member_of_Any`, `Device_Member_of`, `Device_Member_of_Any` and their
negated forms all evaluate to UNKNOWN inside `applies_to`. A rule with
no condition applies to every object referencing the policy.

A mandatory **effective DACL** — a real DACL evaluated through the
full pipeline. An optional **effective SACL**, whose audit ACEs merge
with the object's own during the audit walk. And optional **staged**
DACL and SACL, proposed replacements used for testing.

## Access evaluation

The DACL result is ANDed with the normal evaluation. CAAP can only
restrict, never expand: if the object's DACL grants read and write but
the applicable rule's effective DACL grants only read, the result is
read.

A SACL may carry several scoped policy ACEs, which makes policies
composable — and the AND semantics are what make composition safe,
since each additional policy can only narrow. Inherit-only scoped
policy ACEs do not apply to the object carrying them and are ignored
during lookup. MS-DTYP allows one scoped policy ACE per SACL; KACS
allows several.

For each scoped policy ACE, AccessCheck looks the policy up in the
kernel cache, then for every rule whose `applies_to` is TRUE or absent
evaluates the rule's effective DACL through the full pipeline —
privilege grants, MIC, PIP, the DACL walk, restricted tokens,
confinement — and intersects the result with the running total, which
starts at the normal evaluation's granted mask.

A rule whose condition evaluates FALSE **or UNKNOWN** is skipped. That
is deliberately the opposite of the deny-ACE UNKNOWN rule: skipping is
the conservative choice here, because a rule's DACL can only narrow
what the normal DACL already granted.

If no rules apply — every condition false or unknown, or the policy
has no rules — CAAP has no effect and the normal result stands.

The rule's DACL is evaluated with backup and restore intent **not**
passed: intent is a caller concern, not a policy concern. And CAAP
never recurses. A rule's synthetic descriptor has scoped policy ACEs
stripped before evaluation, so nested CAAP evaluation cannot occur
even when the original SACL carried more of them. The synthetic
descriptor keeps the original owner and group, and preserves the MIC
and PIP labels, so a rule is evaluated against the same mandatory
constraints as the object itself.

## Audit evaluation

For each applicable rule carrying an effective SACL, the rule's audit
ACEs are evaluated alongside the object's own during the audit walk.
They are treated identically — if either says to audit an operation,
it is audited.

The SACL component is purely additive. A CAAP SACL can add audit
coverage and can never suppress auditing the object's own SACL asks
for.

## The policy cache

The kernel keeps a map from policy SID to policy object, empty at
boot. Policies are pushed in through `kacs_set_caap`, which requires
`SeTcbPrivilege` — and marks it used. A non-null spec for an existing
SID replaces the policy; a null spec or zero length removes it. The
policy SID's length is bounded to 8–68 bytes before parsing begins,
and until the cache has been initialised both setting and evaluating
fail with `EACCES`.

The wire format is:

```
[version:u8 = 0x01]
[rule_count:u32le]
per rule:
  [applies_to_len:u32le][applies_to_expr bytes]     (0 = no condition)
  [effective_dacl_len:u32le][effective_dacl bytes]  (MUST NOT be 0)
  [effective_sacl_len:u32le][effective_sacl bytes]  (0 = no audit rules)
  [staged_dacl_len:u32le][staged_dacl bytes]        (0 = no staged DACL)
  [staged_sacl_len:u32le][staged_sacl bytes]        (0 = no staged SACL)
```

All lengths are little-endian `u32`. ACLs use the standard binary
format, and every ACE type valid in a DACL or SACL is permitted inside
a policy ACL. The `applies_to` expression is conditional ACE bytecode,
carrying the same `artx` prefix as callback ACE application data.

The limits are a spec of at most 256 KB, at most 256 rules, an
`applies_to` of at most 64 KB, and an individual ACL of at most 64 KB.
The version byte has to be `0x01`. Trailing bytes after the declared
rules are rejected.

Validation is strict and total. Malformed or truncated `applies_to`
bytecode fails the whole call with `EINVAL` at ingestion rather than
being admitted and later treated as a runtime UNKNOWN — the structural
check happens once, at the boundary. A rule with a zero-length
effective DACL fails the same way, as do truncated fields, lengths
exceeding the buffer, and invalid ACL headers. `SeTcbPrivilege` is
checked before any parsing begins.

authd populates the cache — from the registry on a standalone machine,
from Active Directory on a domain-joined one. The kernel neither knows
nor cares about the source; it is a passive cache. Policies pushed
after services are running do not retroactively affect handles already
opened.

## The recovery policy

When a scoped policy ACE names a SID that is not in the cache — authd
failed to push it, the policy was deleted, the machine is
disconnected — a hardcoded recovery policy is used instead: `GENERIC_ALL`
to BUILTIN\Administrators, to SYSTEM, and to `OWNER RIGHTS`.

Those masks are stored as the literal `GENERIC_ALL` bit rather than
pre-mapped object-specific bits, and are expanded through the caller's
GenericMapping at evaluation time, so the recovery policy works
correctly for every object type.

Because CAAP is an intersection, recovery does not widen access beyond
the object's own DACL: it limits missing-policy access to callers who
also satisfy the recovery DACL. This is a fail-closed recovery mode
with administrator, SYSTEM and owner escape hatches — not a no-effect
fallback.

## Errors

A rule whose DACL evaluation errors denies everything except rights
granted by privileges. Preserving those is the escape hatch: an
administrator with `SeSecurityPrivilege` keeps the ability to read and
modify the SACL and remove the offending scoped policy ACE.

The escape hatch is conditional, though, and the ordering is why. PIP
runs before CAAP and may already have stripped
`ACCESS_SYSTEM_SECURITY` from the privilege-granted set for a
non-dominant caller. The hatch therefore only works for callers who
are PIP-dominant, or where the object carries no trust label.

Rule evaluation swallows every error kind, including allocation
failure, so an out-of-memory condition inside a rule is reported as
"this rule denied all except privileges" rather than as `ENOMEM`.

A rule whose SACL evaluation errors has its audit contribution
skipped, and a diagnostic event is emitted.

## Staging

A rule may carry staged DACLs and SACLs alongside its effective ones,
and AccessCheck evaluates both in parallel. The staged result affects
neither access nor audit; where effective and staged differ, the
difference is reported through a staging mismatch flag returned to the
caller and a diagnostic event.

A rule with no staged DACL contributes its effective result to both
running totals, and a rule with no staged SACL contributes its
effective SACL to both.

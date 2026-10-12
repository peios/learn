---
title: Distribution and recovery
type: concept
description: The kernel CAAP cache and missing-policy recovery exist; automatic distribution, boot-time loading and replication are not implemented.
related:
  - peios/central-access-policies/overview
  - peios/central-access-policies/policies-and-rules
  - peios/central-access-policies/evaluation
  - peios/identity/overview
  - peios/access-decisions/overview
---

The kernel maintains a **policy cache** keyed by policy SID. Access checks
consult it when an object references a central access policy. A missing
entry invokes the recovery policy described below.

> [!IMPORTANT]
> Automatic policy distribution is **not implemented**. Neither authd nor
> peinit loads central access policies from the registry, populates this
> cache at startup, or replicates policies between machines. authd readiness
> does not mean that CAAP policies have been loaded.

The kernel cache, `kacs_set_caap` syscall and access-check enforcement exist.
The integration tests exercise them by calling the syscall directly. This
page describes that kernel mechanism and its recovery behavior, not an
available deployment workflow.

## kacs_set_caap

The syscall is straightforward:

```
kacs_set_caap(policy_sid, sid_len, spec_or_null, spec_len)
```

| Parameter | Meaning |
|---|---|
| `policy_sid` | The SID identifying the policy. An 8–68 byte binary SID. Establishes (or replaces) the cache entry. |
| `sid_len` | The length of the SID in bytes. |
| `spec_or_null` | The wire-format spec to install at this SID. NULL means "remove the policy at this SID from the cache". |
| `spec_len` | The length of the spec in bytes. Zero when removing. |

The call requires enabled `SeTcbPrivilege` in the caller's effective token.
The gate checks token authority, not an executable name. This requirement
does not imply that authd or peinit currently calls it.

The kernel:

1. Validates the SID and the spec. A malformed spec (wrong version byte, truncated fields, too many rules, invalid applies-to bytecode) is rejected with `-EINVAL`. No partial installation; the call is atomic.
2. Parses the spec into the cache's internal representation.
3. Replaces any existing entry at the policy's SID with the new one. If no entry existed, creates one.
4. Returns success.

The policy is now live. The next access check that references this policy SID will see the new version. Existing handles (their access checks already done) are unaffected, per the check-at-open model.

To **remove** a policy, the caller passes NULL for the spec. The kernel deletes the cache entry. Subsequent references to this SID will not find the policy and the recovery policy will apply.

## Who calls kacs_set_caap

There is currently no production distribution caller in authd or peinit.
The test harness calls the syscall directly; there is no public C or Rust
convenience wrapper, configured registry policy store, or cache-query
syscall for management tools.

A future distribution service would need a policy source, update handling,
boot readiness coordination and a recovery workflow. Those are outstanding
implementation and design work, not services that an operator can enable
today by changing a registry value.

## The policy cache and its lifetime

The cache is an in-kernel data structure with the following properties:

- **Empty at boot.** The kernel does not persist the cache across reboots. Every boot starts with an empty cache.
- **Populated by call.** An authorised caller installs policies one at a time via `kacs_set_caap`; the shipped daemons do not do this automatically.
- **Updated in place.** A subsequent push at the same SID replaces the existing entry.
- **Removed by null spec.** A push with a NULL spec deletes the entry.
- **Lives for the lifetime of the running kernel.** A reboot starts over.

The cache is keyed by SID. There is no other index — no name, no category, no version. The SID is the canonical reference, and it must match between the object's `SYSTEM_SCOPED_POLICY_ID_ACE` reference and the cache entry.

## What happens when a policy is missing

A common case during early boot, or when a policy reference outlives the policy itself (the policy was removed but objects still reference it): the SACL of an object contains a `SYSTEM_SCOPED_POLICY_ID_ACE` whose SID does not appear in the policy cache. The kernel needs to do something.

The choice between failing open (treat the missing policy as "no restriction") and failing closed (treat the missing policy as "deny everything") is a security/usability trade-off. Failing open would let administrative misconfiguration silently disable security policies. Failing closed would render objects unreachable when a policy is briefly unavailable.

The kernel picks neither extreme. It applies a **recovery policy** — a hardcoded fallback that grants `GENERIC_ALL` only to:

- `BUILTIN\Administrators`
- `SYSTEM`
- `OWNER_RIGHTS` (the owner of the object, but only if not suppressed by an OWNER RIGHTS ACE in the object's DACL)

The recovery policy is conservative in the sensible direction: ordinary users lose access to objects whose policy is missing, but administrators and SYSTEM retain enough authority to investigate, fix, and restore the policy. Owners can still reach their own objects (with the OWNER RIGHTS caveat).

The recovery policy fires automatically when the kernel cannot find a referenced policy. It applies the same way any other CAAP rule would — its grant is intersected with the running grant from the rest of the pipeline. The intersection ensures that the recovery policy cannot grant more than the DACL would have. In the typical case, a non-administrator user attempting to access an object covered by a missing policy gets nothing (DACL + recovery intersect to empty); an administrator gets whatever the DACL would have given them.

The recovery policy is **not configurable**. It is hardcoded into the kernel. The administrator-and-SYSTEM-only grant is the safe default; administrators who want a different fallback fix the policy distribution problem, they do not change what the recovery policy is.

## The boot sequence

The kernel's CAAP cache starts empty. The current boot sequence does not
populate it, and starting or restarting authd does not change that. An
object referencing an absent policy continues to use the recovery policy.

A dependency on authd readiness cannot establish that a central policy is
loaded. Services must not treat that dependency as a CAAP distribution
barrier. Boot-time policy loading and its readiness contract remain
unimplemented.

## Updates and replication

An explicit `kacs_set_caap` call can replace a local cache entry atomically.
The kernel evaluates later accesses using the cache; existing handles keep
their previously granted rights.

Automatic source watching, registry-to-cache updates and replication
between machines are not implemented. There is no authd CAAP update stream
for management tools to subscribe to. The kernel cache is local to one
running kernel and does not provide persistence or replication itself.

## Cache eviction is administrative

The kernel does not evict cached policies on its own. A policy stays in the cache until:

- `kacs_set_caap` is called with the same SID and a NULL spec (explicit removal).
- The kernel reboots (cache is wiped).

There is no LRU, no size-based eviction, no automatic cleanup. The cache grows or shrinks based only on explicit calls. This is intentional: a policy disappearing from the kernel cache because of memory pressure would be a security issue.

If memory is genuinely tight, the right behaviour is to keep the policies and reduce something else. The kernel's CAAP cache is not where the system's memory pressure should land.

## What CAAP does not get from distribution

A few things distribution does not handle, that are worth knowing:

- **Object-side enforcement.** Distributing a policy makes the policy reachable when an object's SACL references it. The SACL still has to be set up — adding a `SYSTEM_SCOPED_POLICY_ID_ACE` to an object's SACL is a separate administrative action on each object (or a class of objects via a directory-management tool).
- **Audit propagation.** A policy's audit events fire as part of the access check; they go to KMES like any other audit event. The distribution mechanism does not bundle a separate audit pipeline.
- **Per-user policies.** A policy that should apply only to specific users is one whose effective DACL or applies-to expression filters by user identity. Distribution does not target specific users; every policy in the cache applies to whoever accesses an object that references it.

These are policy-author concerns, not distribution concerns. The available kernel interface installs policies by SID into the cache.
An operational distribution layer still needs to be designed and implemented.

## Where to go next

For what the kernel does with a cached policy on each access check, read [Evaluation](~peios/central-access-policies/evaluation).

For the existing boot and identity sequence, read [Boot and trust establishment](~peios/boot-and-trust-establishment/overview); it does not establish CAAP readiness.

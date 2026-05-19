---
title: Distribution and recovery
type: concept
description: Central access policies are distributed by authd into the kernel's policy cache via kacs_set_caap. The cache is empty at boot; until authd populates it, every CAAP reference resolves to the hardcoded recovery policy. This page covers the distribution mechanism, the recovery policy, and the boot-time considerations.
related:
  - peios/central-access-policies/overview
  - peios/central-access-policies/policies-and-rules
  - peios/central-access-policies/evaluation
  - peios/identity/overview
  - peios/access-decisions/overview
---

A central access policy that no one has loaded into the kernel does not affect access checks. The kernel maintains a **policy cache** — a map from policy SID to parsed policy — that AccessCheck consults at step 12. Distributing a policy means getting it into this cache. The mechanism is the `kacs_set_caap` syscall, called by authd.

This page covers how policies get into the kernel, what happens when a referenced policy is missing, and the boot-time sequence that makes the model usable.

## kacs_set_caap

The syscall is straightforward:

```
kacs_set_caap(policy_sid, sid_len, spec_or_null, spec_len)
```

| Parameter | Meaning |
|---|---|
| `policy_sid` | The SID identifying the policy. A 4–68 byte binary SID. Establishes (or replaces) the cache entry. |
| `sid_len` | The length of the SID in bytes. |
| `spec_or_null` | The wire-format spec to install at this SID. NULL means "remove the policy at this SID from the cache". |
| `spec_len` | The length of the spec in bytes. Zero when removing. |

The call requires `SeTcbPrivilege`. The only callers in a running system are authd and peinit; ordinary processes cannot push policies.

The kernel:

1. Validates the SID and the spec. A malformed spec (wrong version byte, truncated fields, too many rules, invalid applies-to bytecode) is rejected with `-EINVAL`. No partial installation; the call is atomic.
2. Parses the spec into the cache's internal representation.
3. Replaces any existing entry at the policy's SID with the new one. If no entry existed, creates one.
4. Returns success.

The policy is now live. The next access check that references this policy SID will see the new version. Existing handles (their access checks already done) are unaffected, per the check-at-open model.

To **remove** a policy, the caller passes NULL for the spec. The kernel deletes the cache entry. Subsequent references to this SID will not find the policy and the recovery policy will apply.

## Who calls kacs_set_caap

**authd** is the primary caller. authd's job is the bridge between policy storage (the registry on a standalone machine, Active Directory on a domain-joined one) and the kernel. On startup:

- authd connects to its source of policy. Standalone: it reads from the registry. Domain-joined: it queries AD via Samba.
- For each policy in the source, authd parses the policy into the wire format and calls `kacs_set_caap` to install it.
- After each policy change in the source (registry write, AD replication), authd re-pushes the affected policy via `kacs_set_caap`.

**peinit** can also call `kacs_set_caap` for early-boot policies that need to be in place before authd starts. This is rare — most of the time, the kernel's CAAP cache is empty until authd takes over.

There is no path for an ordinary application to push a CAAP. The privilege requirement (`SeTcbPrivilege`) and the architectural restriction (only authd and peinit hold it) mean policy authority is concentrated in one place.

## The policy cache and its lifetime

The cache is an in-kernel data structure with the following properties:

- **Empty at boot.** The kernel does not persist the cache across reboots. Every boot starts with an empty cache.
- **Populated by call.** authd (or peinit) pushes policies one at a time via `kacs_set_caap`.
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

The kernel's CAAP cache is empty at boot. Until authd starts and populates the cache, every access check that touches a CAAP-referencing object will get the recovery policy.

This is by design but it has a consequence: **security-sensitive services that depend on CAAP must not start before authd is running**. If a service that handles user requests starts before authd has loaded its policies, the service's access checks will use the recovery policy. For ordinary users accessing the service, that means denial of service. For administrators, that means working but not in the way the intended policies define.

The standard boot order:

1. Kernel initialises. SYSTEM token created. Anonymous token created.
2. peinit starts. peinit may push early-boot policies via `kacs_set_caap` if any exist.
3. authd starts. authd connects to its policy source and pushes every policy via `kacs_set_caap`.
4. authd signals that policy distribution is complete (typically by reaching a steady state).
5. Other services start, knowing the CAAP cache is now populated.

The fourth and fifth steps require coordination — peinit, the service manager, and authd need to agree on when CAAP is ready. The exact mechanism is part of [Boot and trust establishment](~peios/boot-and-trust-establishment/overview).

If your service-start ordering does not respect this, the symptoms are: access denied for ordinary users, mysterious "policy not found" recoveries in the audit log, services that work for administrators but not for anyone else.

## Updates and replication

When a policy changes in the source (an administrator edits a registry value, or AD replicates a new version), authd notices the change and re-pushes the affected policy via `kacs_set_caap`. The cache entry is updated atomically: subsequent access checks see the new version, ones already in progress see whichever version was current at the time they evaluated the relevant step.

There is no kernel notification mechanism for "this policy changed". Tools that want to react to a CAAP update need to subscribe to authd's events or watch the source directly. The kernel itself does not announce.

Replication across machines is authd's job, not the kernel's. The kernel knows nothing about other machines; it sees only the policies authd has pushed locally. On a domain-joined system, each machine's authd reads from AD independently and pushes to its local kernel. Replication latency in AD becomes the propagation delay for CAAP changes across the deployment.

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

These are policy-author concerns, not distribution concerns. The distribution layer is simple: push policies, identified by SID, into a cache the kernel consults. Everything else is the policy author's responsibility.

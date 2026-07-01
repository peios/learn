---
title: The Policy Phase
---

After a source returns `status = ok`, and before minting, authd runs the
**policy phase**: it layers local/system policy onto the source's
resolved principal (§4). The policy phase MAY still deny the logon even
though the credential was valid.

## The assignment model

Privileges and logon rights are **assigned to SIDs** (users or, far more
commonly, groups) by a machine-local **rights-assignment policy** — the
analogue of Windows User Rights Assignment, applied by authd (the seam of
§2.2 keeps assignment in the broker, not the source). Two rules define
how an assignment becomes a token property:

- **Privileges accumulate by union.** A token's *present* privileges are
  the union of the privileges assigned to **every SID in the token** —
  the user SID plus all group SIDs after the merge of step 2 below. There
  is no "deny privilege": a privilege is present iff it is assigned to
  some SID present, otherwise absent.
- **Logon rights are allow/deny, deny overriding.** Each logon type has
  an allow right and a deny right. A principal may perform a logon type
  iff some SID in its set holds the allow right **and no** SID in its set
  holds the deny right. Deny overrides allow.

The rights-assignment *data* is machine-local system policy; populating
and editing that store is tied to the deferred policy-distribution work
(§8). Until it is wired, authd MUST apply the **default assignment table
of §9** (the shipped defaults, analogous to a Windows security template)
and MUST mark tokens minted under it as default-derived in audit. The
default table is a stub to be replaced by the real store; the union and
deny-override *rules* above are permanent.

**Reserved privileges.** `SeCreateTokenPrivilege`, `SeTcbPrivilege`, and
`SeAssignPrimaryTokenPrivilege` MUST NOT appear in any rights-assignment
(default or otherwise) — they are held only by authd and peinit via their
own identity, preserving "authd is the sole minter" (§2.1).
`SeLoadDriverPrivilege` is likewise reserved and **peinit-exclusive**:
PSD-004 MUST-strips it from every non-peinit token, so it appears in no
assignment (not even SYSTEM's), and driver loading routes through peinit.

## Validating the resolved principal

The kernel mints whatever authd assembles — it checks structure, not
authority (PSD-004) — so authd is the authorization boundary and MUST NOT
blindly trust a source. Before the steps below, authd MUST validate the
resolved principal (§4):

- The `user_sid` MUST lie within the **answering source's namespace** —
  for lpsd, `machine_sid`-relative; for a domain source, that domain's
  SID. authd MUST reject (and audit) a resolved principal whose `user_sid`
  is a well-known or built-in SID (SYSTEM `S-1-5-18`, any `S-1-5-32`
  alias, …) or belongs to a different source. A source can thus never
  assert SYSTEM or Administrators *as the principal it authenticated*.
- The source's group SIDs are accepted only as **memberships**. authd
  derives privileges **solely** from its own rights-assignment table
  keyed by SID (the union rule above), **never** from any field of the
  resolved principal — so a malicious membership cannot inject a reserved
  (or any) privilege.
- authd SHOULD bound the group count a source returns; the kernel's 1024
  limit is the hard ceiling (§5.3).

This validation is what contains a compromised source: it can mis-state
its *own* principals, but cannot mint SYSTEM, cross namespaces, or inject
privileges.

## Steps

authd MUST perform these steps in order:

1. **Logon-type rights gate.** Evaluate the allow/deny logon rights
   (above, per the table in §9) for the principal's SID set against this
   logon type. If not permitted, the logon fails with
   `LOGON_TYPE_DENIED` (§6.4) — distinct from a credential failure,
   because it occurs only after the credential is already valid — and
   authd emits a denied audit event.
2. **Merge groups.** Query lpsd for the local groups that contain any of
   the principal's SIDs (including a domain principal's SIDs — §3.2) and
   merge them into the group set. Then add the **implicit groups** for
   this logon type per §9 (Everyone, Authenticated Users, Local, the
   logon-type SID such as Interactive `S-1-5-4`, This Organization
   `S-1-5-15`), each with the `SE_GROUP_*` attributes given there. The
   kernel does NOT add these; authd MUST (PSD-004 §4.4).
3. **Privilege assignment.** Compute the token's present privileges as
   the union over the full SID set, per the default assignment table
   (§9). Set each present privilege's enabled-state per §9 (only
   `SeChangeNotifyPrivilege` enabled by default; all others present but
   disabled).
4. **Integrity level.** Determine the integrity level by the predicate of
   §9 (first match wins): user SID = SYSTEM → System; carries
   `S-1-5-32-544` → High; user SID = local Guest (RID 501) or Anonymous
   (`S-1-5-7`) → Low; otherwise Medium.
5. **Token shaping.** For this version, a single primary token;
   linked/filtered elevation pairs are deferred (§8).
6. **Assemble the token spec** (§5.3): user SID, the merged-and-implicit
   group set with attributes, the union privilege set with
   enabled-states, integrity level, primary group, default DACL, owner,
   claims, mandatory policy, and the POSIX projection. The assembled group
   set MUST be sorted in ascending binary-SID order (§6.4) before minting,
   and `owner_sid_index` / `primary_group_index` (PSD-004) index into that
   sorted array. The logon SID is NOT supplied; the kernel injects it
   (§5.3).

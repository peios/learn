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
  the user SID plus all group SIDs after the group-construction step below.
  There is no "deny privilege": a privilege is present iff it is assigned
  to some SID present, otherwise absent.
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
- The source's group SIDs are accepted only as **memberships**, and only
  those the source is **authoritative to assert**. authd MUST validate
  that every group SID in the resolved principal lies within the
  **answering source's authority** — for lpsd, a `machine_sid`-relative
  SID or one of the local `S-1-5-32` BUILTIN aliases it hosts (§3.1); for
  a domain source, a SID relative to that domain. authd MUST reject (and
  audit) a resolved principal that asserts any group SID outside that set
  — in particular a **domain** source asserting a local BUILTIN alias
  (e.g. `S-1-5-32-544`), any source asserting a well-known privileged SID
  (SYSTEM `S-1-5-18`, the `S-1-5-*` identity/logon SIDs), or a
  foreign-namespace SID. This is the group analogue of the `user_sid`
  check above: a domain principal's local-group membership is authd's to
  resolve via the group-construction step, **never** the domain source's to
  assert.
- Privilege is never itself a field of the resolved principal. authd
  derives privileges **solely** from its own rights-assignment table
  keyed by the **post-merge SID set** (the union rule above), so a
  membership can influence privilege only by naming a SID the source was
  authoritative to assert (validated above) or a local group authd itself
  merged in (step 1) — a source cannot inject a reserved (or any)
  privilege by naming a SID it does not own.
- The `primary_group_sid` MUST be a group SID the source is authoritative
  to assert under the same rule as the `groups` array, and it MUST be
  present in the post-merge group set before the token spec is assembled.
  If not, authd MUST reject the resolved principal and audit the source
  contract violation.
- authd SHOULD bound the group count a source returns; the kernel's 1024
  limit is the hard ceiling (§5.3).
- authd MUST validate every projected POSIX id the source returns before
  using it in the token spec. A non-sentinel id MUST be below 2^31, must lie
  in the band assigned to that SID family (§3.6, §9), and must reverse-map
  to the same SID. For lpsd, a `machine_sid`-relative SID with RID `r` maps
  to `5,000,000 + r`; a local BUILTIN alias `S-1-5-32-N` maps to `1000 + N`.
  `0xFFFFFFFF` is allowed only as the wire sentinel meaning "the source
  assigns no id"; authd MUST resolve it through the idmap before minting, and
  MUST fail the logon if no stable, non-colliding mapping can be produced.
  `0xFFFFFFFF` MUST NOT appear in a KACS token spec.

This validation is what contains a compromised source: it can mis-state
membership among the principals and groups it is genuinely
**authoritative** for — equivalently, it could already achieve that by
editing its own store — but it cannot mint SYSTEM, cross namespaces,
assert a local BUILTIN or well-known privileged SID it does not own, or
otherwise inject privileged membership outside its authority. (Because
lpsd hosts the local `S-1-5-32` aliases, a *compromised lpsd* asserting
local-Administrators membership is within this envelope and gains nothing
over editing its `members` table; the check's bite is on a source
asserting membership **outside** its namespace — the cross-source /
domain vector.)

## Steps

authd MUST perform these steps in order:

1. **Construct the full SID set.** Query lpsd for the local groups that
   contain any of the principal's SIDs (including a domain principal's SIDs
   — §3.2) and merge them into the group set. Then add the **implicit
   groups** for this logon type per §9 (Everyone, Authenticated Users,
   Local, the logon-type SID such as Interactive `S-1-5-4`, This
   Organization `S-1-5-15`), each with the `SE_GROUP_*` attributes given
   there. The kernel does NOT add these; authd MUST (PSD-004 §4.4). This
   post-merge SID set is the input to the logon-rights gate, privilege
   assignment, integrity-level predicate, and token assembly below.
2. **Logon-type rights gate.** Evaluate the allow/deny logon rights
   (above, per the table in §9) for the post-merge SID set against this
   logon type. If not permitted, the logon fails with
   `LOGON_TYPE_DENIED` (§6.4) — distinct from a credential failure,
   because it occurs only after the credential is already valid — and
   authd emits a denied audit event. For the credential-less Service logon
   path of §5.4, this gate is satisfied by the vouching TCB caller until
   the per-service rights-assignment store lands (§8).
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

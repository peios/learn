---
title: Debugging a denial
type: how-to
description: An access was denied and you need to know why. This page is the systematic walk through the access-check pipeline that finds the answer — what to inspect, in what order, and what each finding means.
related:
  - peios/access-decisions/overview
  - peios/access-decisions/mandatory-integrity-control
  - peios/access-decisions/privileges-in-the-pipeline
  - peios/access-decisions/narrowing-layers
  - peios/inspecting/overview
  - peios/auditing/overview
---

A call returned `ACCESS_DENIED`, or a file open failed with `EACCES`, or a registry read came back empty. The access check decided "no", and you need to know which layer of the pipeline produced the denial. This page is the systematic walk.

The pipeline has fifteen steps, but the practical answer almost always falls in one of six categories. This page covers them in the order to check, with the inspection mechanics for each.

## The six places a denial can come from

Before stepping through, the list of candidates:

1. **The token cannot be used.** The thread is impersonating at the Identification level (step 0).
2. **MIC denied it.** The caller's integrity level is below the object's mandatory label, and the policy bits cover the requested category (step 5).
3. **PIP denied it.** The caller's process trust label does not dominate the object's, and the requested right is outside the explicitly-allowed mask (step 5).
4. **The DACL did not grant it.** The walk produced an empty result for the requested bits (step 8).
5. **A narrowing layer stripped it.** Restricted-token pass, confinement, or CAAP removed bits the DACL had granted (steps 10–12).
6. **A privilege was needed and not present, or present and not enabled, or present and missing its intent flag.** Steps 4 and 9 did not pre-decide the bits as granted.

For each of these, this page covers what to look at and what the finding means.

## Find the thread and its tokens

Almost every investigation starts with finding the thread that made the call and inspecting its tokens. The mechanics:

- The thread's primary token: `cat /proc/<pid>/task/<tid>/token` produces a query-only handle (or use `kacs_open_thread_token` programmatically). The handle can be queried with `KACS_IOC_QUERY` for fields including `user_sid`, `groups`, `integrity_level`, `privileges`, `restricted_sids`, `confinement_sid`, `auth_id`, and `impersonation_level`.
- The thread's effective token (impersonation if installed, primary otherwise): `cat /sys/kernel/security/kacs/self` when run from the thread itself; for another thread, the same `/proc/<pid>/task/<tid>/token` path returns the effective token.

For a non-self thread, you need `PROCESS_QUERY_INFORMATION` on the process and PIP dominance. For `/proc/self/token` and `/sys/kernel/security/kacs/self`, the kernel always permits inspection.

With the effective token in hand, several denials are immediately diagnosable:

- **`impersonation_level == Identification`** — the thread is at the wrong impersonation level. AccessCheck on this token denies everything at step 0. Either the client did not request a higher level on the socket, or the two-gate model silently downgraded the impersonation. See [The two-gate model](~peios/impersonation/the-two-gates).
- **`integrity_level` is low and the object is high** — possible MIC denial; check the object's label next.
- **`restricted_sids` is non-empty** — the token is restricted. The denial may be from the restricted-token pass; check what SIDs are in the restricted list.
- **`confinement_sid` is set and `confinement_exempt` is false** — the token is confined. The denial may be from the confinement pass.
- **A privilege you expected to be enabled is in the `present` set but not the `enabled` set** — the privilege is not active; AccessCheck cannot use it.
- **A privilege you expected to be on the token is absent entirely** — authd did not include it; this is a privilege-policy question, not an access-check question.

## Find the object and its SD

Read the security descriptor of the object:

- For files: `kacs_get_sd` on the path. Returns the SD as a self-relative binary blob.
- For registry keys: the equivalent registry API on the key.
- For tokens: query the token handle with the appropriate KACS_IOC_QUERY class.
- For processes: query the PSB.

Parse the SD into its four components (owner, group, DACL, SACL).

The most useful things to read:

- **The owner SID.** Does the caller match? If yes, owner implicit rights apply (unless suppressed — see next).
- **OWNER RIGHTS suppression.** Is there an ACE on `S-1-3-4` (OWNER RIGHTS) in the DACL? If so, the owner's implicit `READ_CONTROL | WRITE_DAC` is suppressed; the owner gets only what that ACE grants.
- **The DACL.** What ACEs are present, in what order? Are there any `INHERIT_ONLY` ACEs that look like they should grant access but are actually skipped during the walk?
- **The mandatory integrity label.** Look for a `SYSTEM_MANDATORY_LABEL_ACE` in the SACL. The SID indicates the object's integrity level; the mask indicates the policy bits.
- **The PIP trust label.** A `SYSTEM_PROCESS_TRUST_LABEL_ACE` in the SACL marks the object as PIP-protected.
- **CAAP references.** `SYSTEM_SCOPED_POLICY_ID_ACE` entries point to central access policies that contribute to the decision.
- **Resource attributes.** `SYSTEM_RESOURCE_ATTRIBUTE_ACE` entries. Relevant if any of the DACL's conditional ACEs references `@Resource.*`.

## Walk the pipeline

With token and SD in hand, walk the pipeline. The questions, in order:

### Impersonation level (pipeline step 0)

Is the effective token an impersonation token at the Identification level? If yes, that is the denial. AccessCheck stops at step 0; no further evaluation occurs. The fix is at the client end: either the client requested Identification (and should have requested Impersonation), or the two-gate model downgraded a higher request to Identification (consult [The two-gate model](~peios/impersonation/the-two-gates)).

### MIC (pipeline step 5)

Is the object's effective mandatory label at a higher level than the token's `integrity_level`?

If yes, look at the label's policy bits. For the bits set, the corresponding rights are pre-decided as denied:

- `NO_READ_UP` → read-category bits are denied.
- `NO_WRITE_UP` → write-category bits are denied (the default for unlabelled objects).
- `NO_EXECUTE_UP` → execute-category bits are denied.

If the requested right falls in a denied category, MIC is the denial. The fix is to either raise the token's integrity (typically by re-authenticating with elevated rights via UAC-style flow) or lower the object's label (requires `SeRelabelPrivilege` for raising, normal SACL access for lowering). Note that a privilege grant from step 4 (SeBackup, SeRestore) **survives** MIC — if MIC blocked write but the caller had `SeRestorePrivilege` with `RESTORE_INTENT`, the write may still succeed.

### PIP (pipeline step 5)

Does the object have a `SYSTEM_PROCESS_TRUST_LABEL_ACE`? If so, look at its SID's type and trust levels and compare to the calling process's PSB.

For dominance: both `pip_type` and `pip_trust` on the caller must be at least the ACE's values. If not, only the rights in the ACE's mask are permitted, and **privilege-granted bits are revoked** (this is the difference between PIP and MIC).

If PIP denied a right, the fix is to run the caller as a more-trusted binary (PIP is about the binary's signature, not about the caller's identity). See [Process integrity protection](~peios/process-integrity-protection/overview).

### Privileges (pipeline steps 4 and 9)

Did the caller need a privilege to get the right? For example, the right is `ACCESS_SYSTEM_SECURITY` (SACL access), or the DACL granted nothing and the caller would need `SeBackup` to read.

Check:

- Is the privilege present on the token?
- Is it enabled?
- Did the caller pass the appropriate intent flag (`BACKUP_INTENT`, `RESTORE_INTENT`)?

If any of those is no, the privilege did not fire. The fix depends on which:

- Privilege absent → authd's privilege policy does not grant this privilege to this principal. A policy-level change, not an access-control change.
- Privilege present but disabled → the calling code should enable it via AdjustPrivileges before the operation.
- Privilege enabled but no intent flag → the calling code should pass the flag in `privilege_intent` to AccessCheck.

### The DACL walk (pipeline step 8)

Run the DACL walk manually, paying attention to:

- **Ordering.** Is the DACL in canonical order (explicit deny, explicit allow, inherited deny, inherited allow)? An out-of-order DACL produces surprising first-writer-wins results.
- **`INHERIT_ONLY` ACEs.** Are there ACEs that look relevant but have the `IO` flag set? They are skipped during the walk.
- **The matching identity.** Does the caller match the SIDs in the ACEs? Remember:
  - The token's `user_sid` matches.
  - Each group in `groups` with `SE_GROUP_ENABLED` set matches for allow ACEs.
  - Groups with `SE_GROUP_USE_FOR_DENY_ONLY` set match for deny ACEs only.
  - The well-known SIDs Everyone, Authenticated Users, etc. match according to their semantics.
  - `OWNER RIGHTS` and `PRINCIPAL_SELF` match per the [virtual group injection](~peios/security-descriptors/ownership) rules.
- **Conditional ACEs.** If any ACE has a conditional expression, evaluate it against the token's claims, the object's resource attributes, and the local claims (if any). A conditional that should evaluate TRUE but evaluates UNKNOWN (because a referenced attribute is missing) does not grant access for an allow ACE.

After the walk, the result is the bits the DACL would grant. If the requested right is missing from this result, the DACL is the denial.

### Narrowing layers (pipeline steps 10–12)

If the DACL granted the right but the final result does not have it, a narrowing layer stripped it. Check each:

- **Restricted-token pass.** If `restricted_sids` is non-empty, walk the DACL using only those SIDs. If the restricted-only result lacks the right, the restricted pass stripped it. (Privileges restored after this pass — privilege-granted bits are immune.)
- **Confinement.** If the token is confined, walk the DACL using `confinement_sid` and `confinement_capabilities`. If that result lacks the right, confinement stripped it. (Privileges are not restored — they can be lost here.)
- **CAAP.** If the SACL has `SYSTEM_SCOPED_POLICY_ID_ACE` entries, look up each referenced policy and evaluate its rules. If any rule's effective DACL would not have granted the right, CAAP stripped it. The recovery policy applies if a referenced policy is missing from the kernel cache.

### Audit (pipeline steps 13–14)

If the steps above did not produce a clear answer, check the audit log. The access check emits audit events that record:

- The requested mask, the granted mask.
- Which privileges contributed (and whether they survived).
- The matched ACE (for SACL-driven audits).
- The subject and process.

A `privilege-use` event with `success=false` tells you a privilege fired and was stripped — that points at confinement/CAAP/PIP. An `access-audit` event with `success=false` and a DACL-walk trigger tells you the DACL did not grant. The audit trail is often the fastest way to localise a denial.

## A compact checklist

When a denial happens, in order:

1. Find the thread (`tid`, `pid`).
2. Read the effective token. Note `user_sid`, `integrity_level`, `restricted_sids`, `confinement_sid`, `impersonation_level`, and which privileges are present-and-enabled.
3. Read the object's SD. Note the owner, the DACL contents (with attention to order and `INHERIT_ONLY`), the mandatory label, the PIP label, and any CAAP references or conditional ACEs.
4. Walk the pipeline mentally against these inputs.
5. Check the audit log if the manual walk does not point at a single layer.

Most denials are diagnosed at step 4 with one of the six categories listed at the top. The remainder are either edge cases (a conditional ACE evaluating UNKNOWN because of a missing claim, a CAAP policy with a misconfigured applies-to expression) or programming bugs (the wrong token installed, an incorrect intent flag, a hand-built SD with bad ordering).

## When to use the access-check syscall directly

For complex investigations, calling `kacs_access_check` directly is the precise tool. The syscall takes the token, the SD, the desired mask, and all the optional parameters (privilege_intent, self_sid, local_claims, object_audit_context, pip_type/pip_trust). It returns the granted mask, the continuous-audit mask, and the staging-mismatch flag.

You can call it from a debugging tool with the exact inputs the failing code used and see what comes back. The granted mask tells you which bits ended up granted; the audit emissions tell you which layers fired. A denial that is inscrutable from logs becomes visible from a manual access-check invocation with a known set of inputs.

This is how authoritative diagnoses work for the hard cases: reproduce the access check inputs, call the syscall manually, examine the output.

---
title: Staged policies
type: concept
description: A CAAP rule can carry a staged DACL and SACL alongside its effective ones. The staged versions are evaluated in parallel during AccessCheck but do not affect the granted mask. The staging mismatch flag signals when the staged version would have produced different behaviour. This page covers how staging works and the rollout pattern it enables.
related:
  - peios/central-access-policies/overview
  - peios/central-access-policies/policies-and-rules
  - peios/central-access-policies/evaluation
  - peios/central-access-policies/distribution-and-recovery
---

Rolling out a change to a central access policy is operationally risky in a way that local DACL changes are not. A DACL change affects one object; if it is wrong, one object misbehaves. A CAAP change affects every object that references the policy — potentially thousands of files, registry keys, or service endpoints. An overly-permissive change is a security incident; an overly-restrictive change is a system-wide outage.

**Staged policies** are the testing primitive that makes CAAP rollout safe. A CAAP rule can carry, alongside its `effective_dacl` and `effective_sacl`, a proposed replacement called the `staged_dacl` and `staged_sacl`. During AccessCheck, the kernel evaluates both versions in parallel. The effective version is what affects the granted mask; the staged version does not. But the kernel records whether the staged version would have produced different behaviour, and reports that as a **staging mismatch** flag in the access check's output.

A staging mismatch is a signal: "if this staged change had been live, this access would have gone differently". Administrators can collect mismatches over a representative period of access traffic and make an informed decision about whether to commit the staged version.

This page covers how staging works mechanically, what the mismatch flag means, and the rollout pattern it enables.

## How staging fits into evaluation

When the kernel evaluates a CAAP rule at step 12 of the pipeline:

1. The rule's applies-to expression is evaluated. If it returns FALSE or UNKNOWN, the rule is skipped entirely; no effective evaluation, no staged evaluation.
2. If the applies-to returned TRUE, the `effective_dacl` is evaluated against the calling token. The result is intersected with the running grant.
3. If the rule has a `staged_dacl`, the kernel **also** evaluates it against the same token. The result is **not** intersected with anything; the running grant uses only the effective result.
4. The kernel compares the staged result against the effective result. If they differ — that is, the staged DACL would have granted a different mask than the effective DACL did — the access check's **staging mismatch flag** is set.
5. The same comparison happens for the `staged_sacl` versus `effective_sacl`: if the staged audit ACEs would have produced different events (a different set of audits fired, or different bits triggered them), the staging mismatch flag is also set.

The mismatch flag is a boolean per access check. It does not say which rule or policy caused the mismatch; that level of detail would require richer reporting. What it does say is: somewhere in the CAAP layer of this access check, a staged change would have made a difference.

Tools watching the flag can correlate it with the call's parameters (which token, which object, which requested rights) to localise where staging would have changed behaviour. This is enough for an administrator to make a go/no-go decision on a policy rollout.

## What the mismatch flag is and is not

The flag is **informational**. It does not change behaviour — the access check returned the granted mask the effective policy produced, and the caller's operation proceeds accordingly. The flag is for observers (audit systems, deployment tools, monitoring dashboards).

The flag is **boolean**. It says "yes, somewhere a staged version differed from the effective" or "no, the staged versions all produced identical results". It does not enumerate which rules differed, what they granted, or what specifically was different. Richer staging diagnostics are a job for the test pipeline (running representative AccessCheck calls and recording the differences); the kernel's report is the existence of a difference, not its detail.

The flag is **per access check**. Each access check call produces its own flag value in its own output. Aggregating mismatches across many calls is the consumer's job.

## The DACL mismatch

A DACL staging mismatch is set when the staged_dacl produces a different granted mask than the effective_dacl for the same call.

The comparison is bit-exact. If the effective DACL would grant `FILE_READ_DATA | FILE_READ_ATTRIBUTES` and the staged DACL would grant only `FILE_READ_DATA`, that is a mismatch. If both would grant the same bits, no mismatch. Bits not present in either grant are irrelevant.

The asymmetry is honest: a staged DACL more permissive than the effective would also trigger a mismatch. Staging is not about "this would deny more"; it is about "this would behave differently".

## The SACL mismatch

The SACL mismatch is more subtle because SACL evaluation produces audit *events*, not granted bits. The staged_sacl mismatch is set when the staged SACL would have produced a different set of audit events for the same call than the effective SACL did.

"Different set" means: the union of events that would have fired from the staged SACL is not equal to the union from the effective SACL. An event in one but not the other, or vice versa, is a mismatch. This includes audit ACE matches that would have triggered, and conditional audit ACEs whose conditional expressions differ.

The mismatch records the delta — what events the effective version emitted versus what the staged version would have emitted — though the bit in the flag is just "differ" or "do not differ".

## The rollout pattern

The intended deployment flow for a CAAP change:

1. **Author the staged change.** Take the existing policy. Add or modify the `staged_dacl` and/or `staged_sacl` to reflect the proposed change. Leave the effective versions unchanged.
2. **Distribute the policy.** authd pushes the policy (with staged versions populated) to the kernel via `kacs_set_caap`. Other machines in the deployment get the same policy through their authd instances.
3. **Run for a period.** The system runs normally. Every access check produces a granted mask; tokens behave as if the effective version is in force. The mismatch flag is set whenever the staged version would have produced different behaviour.
4. **Collect mismatch reports.** A monitoring tool records mismatches and their contexts (which call, which token, which object, which requested rights). Administrators review the report.
5. **Decide.** If the mismatches reflect intended behaviour changes (the change tightens access in exactly the cases the administrator expected to tighten), the change is good. If unexpected accesses are flagged, the change has unintended side effects and needs revision.
6. **Commit.** Replace the policy with one where `effective_dacl` and `effective_sacl` hold what the staged versions held. Push via `kacs_set_caap`. The change is now live; subsequent access checks use the new effective version.
7. **Optionally, drop the staging fields.** Once the change is committed, the policy can be re-pushed without staged fields, or with new staged fields representing the next planned change.

This flow lets administrators see the effect of a CAAP change on real traffic before committing. The mismatch flag turns "what will this change do?" from a question requiring synthetic test data into an observation of the actual system.

## Staging applies to one rule, not whole policies

Each rule in a policy can have its own staged DACL and SACL. The staging is per-rule, not per-policy. A policy with three rules can have one rule staging a change while the other two stay aligned (no staged version, or staged equal to effective). The mismatch is set whenever any active rule's staged version differs from its effective version.

Operationally, this is exactly what you want. A policy administrator typically wants to stage one change at a time, not stage the whole policy. The rule-level granularity lets each change be reasoned about independently.

## What staging does not do

A few clarifications:

- **Staging does not affect access.** The staged DACL never contributes to the granted mask. Whatever the effective version returns is what the caller gets.
- **Staging does not affect audit events.** The staged SACL does not fire events; only the effective SACL does. The staged SACL is evaluated only for the comparison.
- **Staging is not versioning.** There is no "previous staged" or "next staged". Each rule has at most one staged DACL and one staged SACL. Replacing them replaces them.
- **Staging is not a rollback mechanism.** If a committed change turns out to be wrong, the rollback is to re-author the policy with the old version and push it again. The staging fields are forward-looking, not backward-looking.

## How staging changes for the audit consumer

An audit consumer that wants to use staging meaningfully should look for the staging mismatch flag in audit events. The flag's presence is a signal to investigate; the access in question would have been decided differently under the proposed change.

Aggregating mismatches over time and bucketing them by (token, object class, requested rights) gives the administrator a picture: "the proposed change would have denied N accesses, of which M look intentional and (N-M) look unintentional". From there, deciding whether to commit is straightforward.

Without staging, the equivalent diagnostic is impossible without either a parallel test system or an A/B rollout — both expensive. Staging makes the comparison free per access check.

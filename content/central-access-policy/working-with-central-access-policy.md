---
title: Working with Central Access Policy
type: how-to
order: 110
description: Applying, removing, staging, and diagnosing Central Access Policies on objects using the sd tool.
---

Central Access Policies are managed centrally and applied to objects via scoped policy ACEs.

## Apply a policy to an object

Add a scoped policy ACE to the object's SACL. This requires `SeSecurityPrivilege`:

```
$ sd cap apply /srv/data/finance "Finance Data Policy"
```

The object is now governed by the Finance Data Policy in addition to its own DACL.

## Apply multiple policies

```
$ sd cap apply /srv/data/finance "Finance Data Policy"
$ sd cap apply /srv/data/finance "Compliance Retention Policy"
```

Both policies are evaluated. Each can only further restrict — the intersection of all policies and the object's DACL determines the final result.

## View applied policies

```
$ sd cap list /srv/data/finance
Applied policies:
  Finance Data Policy          S-1-17-...-1001   (effective)
  Compliance Retention Policy  S-1-17-...-1002   (effective, staged)
```

The output shows each policy by name and SID, and whether it has a staged DACL pending.

## Remove a policy from an object

```
$ sd cap remove /srv/data/finance "Compliance Retention Policy"
```

The scoped policy ACE is removed from the SACL. The object is no longer governed by that policy.

## Test a policy change with staging

Before enforcing a new policy, stage it to see the impact:

**1. Deploy the staged DACL.** This is done centrally — update the policy definition to include a staged DACL alongside the current effective DACL. The staged DACL is distributed to all machines via the normal policy distribution mechanism.

**2. Review the impact.** AccessCheck evaluates both DACLs in parallel and logs differences. Check the audit logs:

```
$ sd cap audit /srv/data/finance
Staging differences for "Finance Data Policy":
  /srv/data/finance/q4-report.pdf
    alice: effective=READ|WRITE  staged=READ
    bob:   effective=READ        staged=READ        (no change)
  /srv/data/finance/budgets/
    contractors: effective=READ  staged=DENIED
```

The output shows exactly which users would gain or lose access if the staged DACL became effective.

**3. Adjust if needed.** Update the staged DACL centrally and re-check.

**4. Promote.** Replace the effective DACL with the staged DACL in the policy definition. The change takes effect immediately on all objects that reference the policy.

## Troubleshoot missing policies

If access is unexpectedly broad, a policy may be missing from the kernel cache:

```
$ sd cap status
Policy cache:
  Finance Data Policy          S-1-17-...-1001   loaded
  Compliance Retention Policy  S-1-17-...-1002   MISSING — recovery policy active
```

A missing policy means the recovery policy is in effect — the object's own DACL is the only restriction. Investigate why the policy was not loaded:

- Is the machine connected to the domain?
- Did the authentication service start successfully?
- Was the policy deleted from the directory?

Once the underlying issue is resolved, the policy is reloaded into the cache and enforcement resumes.

## Diagnose CAP in access decisions

`sd explain` shows CAP evaluation as part of the pipeline:

```
$ sd explain /srv/data/finance/q4-report.pdf 2041 FILE_WRITE_DATA
...

[8] Central Access Policy
    Policy: Finance Data Policy (S-1-17-...-1001)
    Applies-to: @Resource.department == "finance" — true
    Effective DACL walk:
      Allow  Finance      FILE_READ_DATA
             SID match: no — skip
      Allow  Compliance   FILE_READ_DATA | FILE_WRITE_DATA
             SID match: no — skip
    CAP grants: none

    Normal evaluation granted: FILE_WRITE_DATA
    CAP evaluation granted:   (none)
    Intersection:             DENIED

Result: DENIED — Central Access Policy denied FILE_WRITE_DATA
```

The normal DACL granted write access, but the CAP's effective DACL did not — so the intersection is empty and the write is denied.

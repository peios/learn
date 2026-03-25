---
title: Troubleshooting Common Issues
type: how-to
order: 20
description: Fixing broken ACL inheritance, missing audit events, and other frequently encountered security configuration problems.
---

## Missing or broken inheritance

**Symptom:** A file or directory does not have the ACEs you expect from its parent.

**Check whether inheritance is broken:**

```
$ sd show /srv/data/projects/secret.txt
DACL:
  Allow  alice  FILE_ALL_ACCESS  (explicit)
```

No inherited ACEs — inheritance may have been broken on this object.

**Check the parent's inheritable ACEs:**

```
$ sd show /srv/data/projects
DACL:
  Allow  Developers  FILE_READ_DATA | FILE_WRITE_DATA  (CI | OI)
  Allow  Domain Users  FILE_READ_DATA                   (CI | OI)
```

The parent has inheritable ACEs, but the child doesn't have them. Inheritance was broken.

**Fix — re-enable inheritance:**

```
$ sd inherit /srv/data/projects/secret.txt
```

**Fix — propagate parent changes to existing children:**

If the parent's DACL was changed after children were created, existing children retain their old inherited ACEs. To push the parent's current inheritable ACEs to all children:

```
$ sd propagate /srv/data/projects
```

This re-evaluates inheritance for every child in the tree, replacing their inherited ACEs with the parent's current inheritable ACEs. Explicit ACEs on children are preserved.

## Audit events not appearing

**Symptom:** You set audit rules on an object but no events appear in the audit log.

### Check that audit ACEs exist

```
$ sd show /srv/data/finance/accounts.db
...
SACL:
  Audit  Everyone  FILE_WRITE_DATA  (success)
```

If the SACL is empty or has no audit ACEs, no events will be generated.

### Check the success/failure flags

An audit ACE with only the `success` flag will not fire on denied access. If you expect to see failed access attempts, add the `failure` flag:

```
$ sd audit add /srv/data/finance/accounts.db \
    audit Everyone FILE_WRITE_DATA success,failure
```

### Check the access mask

An audit ACE for `FILE_WRITE_DATA` will not fire on read operations. Make sure the mask covers the operations you want to audit.

### Check conditional expressions

If the audit ACE has a conditional expression, the expression may not be evaluating to true:

```
SACL:
  Audit  Everyone  FILE_WRITE_DATA  (success)
    IF (@Resource.classification == "confidential")
```

If the object has no `classification` resource attribute, the expression evaluates to UNKNOWN. Unlike DACL conditional ACEs, audit conditional ACEs **do** fire on UNKNOWN — so check whether the attribute exists and has the expected value:

```
$ sd attr /srv/data/finance/accounts.db
(no attributes)
```

### Check the event daemon

If audit ACEs are correctly configured but events still do not appear, the issue may be in the event pipeline:

```
$ peiosctl status eventd
eventd: running (PID 61)
```

If eventd is not running, events are buffered in the kernel ring buffer but not persisted. They will be delivered when eventd starts — unless the buffer overflows, in which case events may be dropped depending on the overflow policy.

### Check per-token audit policy

Per-token audit policy can generate events independently of object SACLs. If you see unexpected events (or expect events from a specific principal), check the token:

```
$ idn show 2041
...
Audit Policy:
  FILE_WRITE_DATA  success,failure  (all objects)
```

This token audits all writes everywhere — regardless of the object's SACL.

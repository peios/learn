---
title: Transferring Ownership of an Object
type: how-to
order: 150
description: How to view, transfer, or take ownership of an object, and the recovery path for locked-out objects.
---

Use `sd owner` to view or change the owner of an object.

> [!NOTE]
> **Prerequisites:** WRITE_OWNER on the target object to transfer ownership, or `SeTakeOwnershipPrivilege` to claim ownership regardless of the DACL.

## View the current owner

```bash
$ sd owner /srv/data/reports
S-1-5-21-...-1013 (alice)
```

## Transfer ownership

If you have `WRITE_OWNER` access on the object, you can set a new owner:

```bash
$ sd owner /srv/data/reports bob
```

Bob is now the owner. As owner, Bob receives implicit READ_CONTROL and WRITE_DAC — he can read the security descriptor and modify the DACL.

## Take ownership

If you cannot access the object at all but hold `SeTakeOwnershipPrivilege`, you can claim ownership:

```bash
$ sd owner /srv/data/reports --take
```

This sets you as the owner regardless of the current DACL. The privilege must be enabled on your token.

## Recovering a locked-out object

A misconfigured DACL can lock everyone out. The recovery path is always the same:

1. **Take ownership** using `SeTakeOwnershipPrivilege`:

```bash
$ sd owner /srv/data/reports --take
```

2. **Verify you are the owner** — as owner, you now have READ_CONTROL and WRITE_DAC:

```bash
$ sd show /srv/data/reports
Owner:  S-1-5-21-...-500 (Administrator)
...
```

3. **Fix the DACL**:

```bash
$ sd set /srv/data/reports \
    allow alice FILE_ALL_ACCESS \
    allow "Domain Users" FILE_READ_DATA
```

Taking ownership does not grant access to the object's contents — it only grants control over the security policy. You must fix the DACL before anyone can read or write the object through normal means.

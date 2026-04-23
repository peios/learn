---
title: Using OWNER RIGHTS to Restrict or Expand Owner Access
type: how-to
description: How to use the OWNER RIGHTS ACE (S-1-3-4) to override the default rights granted to an object's owner.
---

By default, the owner of an object receives `READ_CONTROL` and `WRITE_DAC` implicitly. An **OWNER RIGHTS ACE** overrides these defaults — granting exactly the rights it specifies, no more.

> [!NOTE]
> **Prerequisites:** WRITE_DAC on the target object.

OWNER RIGHTS uses the well-known SID `S-1-3-4`. It can be referenced by name in `sd` commands.

## Restrict the owner

To prevent the owner from modifying the DACL:

```bash
$ sd add /srv/data/policy.conf allow "OWNER RIGHTS" READ_CONTROL
```

The owner can now read the security descriptor but cannot change the DACL. The default WRITE_DAC is no longer granted — the OWNER RIGHTS ACE replaces the defaults entirely.

This is useful for objects where an administrator sets the access policy and the owner should not be able to override it.

## Expand the owner's rights

To grant the owner additional rights beyond the defaults:

```bash
$ sd add /srv/data/workspace allow "OWNER RIGHTS" "READ_CONTROL | WRITE_DAC | DELETE"
```

The owner can now read the SD, modify the DACL, and delete the object. Without this ACE, DELETE would require an explicit allow ACE in the DACL.

## Remove OWNER RIGHTS

Removing the OWNER RIGHTS ACE restores the default behavior — the owner receives READ_CONTROL and WRITE_DAC implicitly:

```bash
$ sd remove /srv/data/policy.conf allow "OWNER RIGHTS" READ_CONTROL
```

## Verify the effect

Check what the owner actually gets:

```bash
$ sd show /srv/data/policy.conf
Owner:  S-1-5-21-...-1013 (alice)

DACL:
  Allow  S-1-3-4 (OWNER RIGHTS)   READ_CONTROL
  Allow  Domain Users              FILE_READ_DATA
  Allow  Administrators            FILE_ALL_ACCESS
```

Alice owns this object but can only read the security descriptor. She cannot modify the DACL or access the file's contents unless another ACE grants it — in this case, she would need to also be a member of Domain Users or Administrators.

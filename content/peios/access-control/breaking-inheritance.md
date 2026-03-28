---
title: Breaking Inheritance on an Object
type: how-to
order: 140
description: How to disconnect an object from its parent's DACL by breaking, clearing, or re-enabling inheritance.
---

By default, objects inherit ACEs from their parent. When an object needs different permissions from the rest of the tree, you can **break inheritance** — disconnecting the object from its parent's DACL.

> [!NOTE]
> **Prerequisites:** WRITE_DAC on the target object.

## Break inheritance and keep existing rules

```bash
$ sd break /srv/data/reports/sensitive.txt --copy
```

This breaks inheritance and converts all inherited ACEs into explicit ACEs. The permissions are identical to what they were before — but they are now local to the object and can be individually edited without affecting or being affected by the parent.

Before:
```bash
$ sd show /srv/data/reports/sensitive.txt
DACL:
  Allow  alice          FILE_ALL_ACCESS        (explicit)
  Allow  Domain Users   FILE_READ_DATA         (inherited, CI | OI)
```

After:
```bash
$ sd show /srv/data/reports/sensitive.txt
DACL:
  Allow  alice          FILE_ALL_ACCESS        (explicit)
  Allow  Domain Users   FILE_READ_DATA         (explicit)
```

Both ACEs are now explicit. Changes to the parent directory's DACL will no longer affect this file.

## Break inheritance and start fresh

```bash
$ sd break /srv/data/reports/sensitive.txt --clear
```

This breaks inheritance and removes all inherited ACEs. Only the existing explicit ACEs remain.

```bash
$ sd show /srv/data/reports/sensitive.txt
DACL:
  Allow  alice          FILE_ALL_ACCESS        (explicit)
```

The inherited allow for Domain Users is gone. Use this when the object's permissions should be completely independent of the parent.

## Re-enable inheritance

To reverse a broken inheritance and reconnect to the parent:

```bash
$ sd inherit /srv/data/reports/sensitive.txt
```

This re-enables inheritance, replacing the object's inherited ACEs with the current inheritable ACEs from the parent. Explicit ACEs on the object are preserved.

```bash
$ sd show /srv/data/reports/sensitive.txt
DACL:
  Allow  alice          FILE_ALL_ACCESS        (explicit)
  Allow  Domain Users   FILE_READ_DATA         (inherited, CI | OI)
```

The parent's inheritable ACEs flow down again.

## When to break inheritance

Breaking inheritance is the right approach when an object genuinely needs different permissions from its siblings. Common cases:

- A sensitive file in a broadly accessible directory
- A subdirectory with a different team's access requirements
- A configuration file that only the owning service should read

If you find yourself breaking inheritance on many objects in the same directory, that may be a sign that the parent's DACL needs restructuring rather than each child needing an exception.

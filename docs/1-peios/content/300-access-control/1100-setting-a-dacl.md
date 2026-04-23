---
title: Setting a DACL on a File or Directory
type: how-to
description: How to use sd set to replace explicit ACEs on an object while preserving inherited ACEs.
---

Use `sd set` to replace the DACL on an object. This sets the complete list of explicit ACEs — any existing explicit ACEs are replaced.

> [!NOTE]
> **Prerequisites:** WRITE_DAC on the target object, or ownership (which grants WRITE_DAC by default).

## Set a DACL

```bash
$ sd set /srv/data/reports \
    deny bob FILE_WRITE_DATA \
    allow "Domain Users" FILE_READ_DATA \
    allow alice FILE_ALL_ACCESS
```

Each rule is specified as a type (`allow` or `deny`), a principal (by name or SID), and one or more rights. Multiple rules are listed in sequence.

The tool places ACEs in canonical order automatically — deny ACEs before allow ACEs — regardless of the order you specify them on the command line.

## Referencing principals

Principals can be referenced by name or by SID:

```bash
$ sd set /srv/data/reports \
    allow "Domain Users" FILE_READ_DATA \
    allow S-1-5-21-...-1013 FILE_ALL_ACCESS
```

Names are resolved to SIDs before being written. The stored ACE always contains the SID.

## Setting inheritance flags

To make ACEs inheritable, add inheritance flags after the rights:

```bash
$ sd set /srv/data/projects \
    allow "Domain Users" FILE_READ_DATA ci,oi \
    allow Developers "FILE_READ_DATA | FILE_WRITE_DATA" ci,oi \
    allow Auditors FILE_READ_DATA ci,oi,io
```

| Flag | Meaning |
|---|---|
| `ci` | Container Inherit — propagates to child directories |
| `oi` | Object Inherit — propagates to child files |
| `np` | No Propagate — inherits to direct children only |
| `io` | Inherit Only — does not apply to this object, only its children |

Without inheritance flags, ACEs apply only to the object itself and are not inherited by children.

## Inherited ACEs are preserved

Setting a DACL replaces only the **explicit** ACEs — the ones set directly on the object. Inherited ACEs from the parent remain unless you explicitly break inheritance.

Before:
```bash
$ sd show /srv/data/reports
DACL:
  Allow  alice          FILE_ALL_ACCESS                    (explicit)
  Allow  Domain Users   FILE_READ_DATA                     (inherited, CI | OI)
```

After setting:
```bash
$ sd set /srv/data/reports \
    allow alice FILE_ALL_ACCESS \
    allow bob FILE_READ_DATA

$ sd show /srv/data/reports
DACL:
  Allow  alice          FILE_ALL_ACCESS                    (explicit)
  Allow  bob            FILE_READ_DATA                     (explicit)
  Allow  Domain Users   FILE_READ_DATA                     (inherited, CI | OI)
```

The explicit ACEs changed. The inherited ACE from the parent is still there.

## Verify after setting

Always verify the result with `sd show` after modifying a DACL:

```bash
$ sd show /srv/data/reports
```

This confirms the ACEs are in the expected order and inherited ACEs were preserved.

---
title: Setting and Changing Mandatory Labels
type: how-to
order: 110
description: Viewing, setting, changing, and removing mandatory integrity labels on objects using the sd label command.
---

Use `sd label` to view, set, or change the mandatory integrity label on an object.

> [!NOTE]
> **Prerequisites:** `SeRelabelPrivilege` required to set or change mandatory labels.

## View an object's label

```bash
$ sd label /srv/data/sensitive.db
High (no-write-up)
```

If the object has no explicit label, it reports the default:

```bash
$ sd label /srv/data/notes.txt
Medium (default, no explicit label)
```

## Set a label

```bash
$ sd label /srv/data/sensitive.db high
```

This adds a mandatory label ACE to the object's SACL, setting its integrity level to High. Processes running below High integrity cannot write to this object.

## Restrict read and execute

By default, a mandatory label only restricts write access. To also block read or execute from lower-integrity processes:

```bash
$ sd label /srv/data/sensitive.db high --restrict write,read
```

Now processes below High integrity cannot read or write the object. The `--restrict` flag accepts any combination of `write`, `read`, and `execute`.

## Change an existing label

Setting a label on an object that already has one replaces it:

```bash
$ sd label /srv/data/sensitive.db system
```

The label changes from High to System.

## Remove a label

To remove the mandatory label and return to the default (Medium):

```bash
$ sd label /srv/data/sensitive.db --remove
```

## Required privilege

Setting or changing a mandatory label requires `SeRelabelPrivilege`. This privilege is not held by ordinary users — integrity labels are system policy, not something object owners can set at their discretion.

```bash
$ sd label /srv/data/notes.txt high
Error: SeRelabelPrivilege required

$ idn privileges --enabled
SeRelabelPrivilege    not present
```

An administrator with the appropriate privilege must set the label.

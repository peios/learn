---
title: Adding Allow and Deny Rules
type: how-to
order: 130
---

Use `sd add` to add individual ACEs to an existing DACL without replacing the other rules.

## Add an allow rule

```
$ sd add /srv/data/reports allow contractors FILE_READ_DATA
```

This adds a single allow ACE for the contractors group. Existing ACEs are preserved.

## Add a deny rule

```
$ sd add /srv/data/reports deny intern FILE_WRITE_DATA
```

The tool places the deny ACE in canonical position — before the allow ACEs — regardless of the existing DACL contents.

## Add an inheritable rule

Include inheritance flags to make the new ACE propagate to children:

```
$ sd add /srv/data/projects allow contractors FILE_READ_DATA ci,oi
```

## Add multiple rules at once

```
$ sd add /srv/data/reports \
    allow contractors FILE_READ_DATA \
    deny intern "FILE_WRITE_DATA | FILE_DELETE_CHILD"
```

All specified ACEs are added and the DACL is reordered to maintain canonical ordering.

## Remove a rule

Use `sd remove` to pull a specific ACE out of the DACL. Specify the type, principal, and rights to match:

```
$ sd remove /srv/data/reports allow contractors FILE_READ_DATA
```

This removes the ACE that matches all three — type, principal, and rights. If no exact match is found, the command fails without modifying the DACL.

## A practical example

A project directory currently grants read access to Domain Users. A new contractor needs read access, but an intern on the team should not be able to modify anything:

```
$ sd show /srv/data/project-x
DACL:
  Allow  Developers    FILE_READ_DATA | FILE_WRITE_DATA   (CI | OI)
  Allow  Domain Users  FILE_READ_DATA                     (CI | OI)

$ sd add /srv/data/project-x \
    deny intern FILE_WRITE_DATA \
    allow contractors FILE_READ_DATA

$ sd show /srv/data/project-x
DACL:
  Deny   intern         FILE_WRITE_DATA
  Allow  Developers     FILE_READ_DATA | FILE_WRITE_DATA   (CI | OI)
  Allow  Domain Users   FILE_READ_DATA                     (CI | OI)
  Allow  contractors    FILE_READ_DATA
```

The deny for the intern is placed first in canonical order. The allow for contractors is placed after the existing allows. The original ACEs are untouched.

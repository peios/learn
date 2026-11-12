---
title: Conformance
description: Every requirement of this chapter collected by role — the provider and the applier.
---

## A conforming provider

**The file.** Ships it at `/usr/share/skeleton` as an ordinary payload
file, in UTF-8 text (§11.3).

**Entries.** Writes only the three entry shapes, with absolute,
canonical paths outside `/usr`, each path once (§11.3).

**Order.** Lists each entry after its parent, which is the root or an
earlier directory entry (§11.3).

**Links.** Gives each link a relative target that stays inside the root
(§11.3).

**Descriptors.** Writes descriptors in SDDL without spaces, naming
principals by well-known SIDs or absolute aliases, and granting SYSTEM a
right to read each directory (§11.3).

## A conforming applier

**When.** Applies the root's own file, after installing the root's
packages and before running anything from it (§11.4).

**Checking.** Rejects the whole file on any error, before making
anything (§11.4).

**Making.** Makes each missing entry in order. Leaves an existing
directory, or an existing link with the same target, as it is. Fails
on anything else at an entry's path, and reports the entry. Never
follows a link, deletes anything, or changes what it finds (§11.4).

**Descriptors.** Creates a directory that has a descriptor with that
descriptor in the same operation, never afterwards. Where the tree
cannot hold descriptors, creates the directory without one (§11.4).

**No file.** Warns when the root has no skeleton file (§11.4).

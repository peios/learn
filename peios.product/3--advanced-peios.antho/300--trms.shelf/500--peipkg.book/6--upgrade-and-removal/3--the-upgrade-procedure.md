---
title: The Upgrade Procedure
description: The preconditions an upgrade adds to an install's, the steps it runs, and what happens to the upgraded package's dependents.
---

## Preconditions

Every install precondition (§5.1) holds for the new version, except that
"not already installed" is replaced by "the installed version has the
same name and architecture, in the same root, at a different version".

In addition: the new version's dependencies are satisfied, or will be by
other operations in the same transaction; no installed package depends
on the current version in a way the new version cannot satisfy; and a
downgrade carries an explicit authorisation.

## The steps

1. **Validate** the new package exactly as an install does (§5.2).
2. **Diff** the old file list against the new (§6.1).
3. **Stage** every added and replaced file to a temporary sibling of its
   destination, verifying its content hash.
4. **Apply**, at commit: rename added files in; rename replaced
   originals aside and the staged files in; rename removed files aside.
5. **Schedule side effects**, including those implied by files being
   removed as well as those the new version declares.
6. **Re-register**: replace the database's record for this package with
   the new version's identity, file list, and manifest.

## Dependents

An upgrade that would leave a dependent's constraints unsatisfied cannot
proceed on its own. The resolver includes the dependent's upgrade — or
its removal — in the same transaction, or the resolution fails.

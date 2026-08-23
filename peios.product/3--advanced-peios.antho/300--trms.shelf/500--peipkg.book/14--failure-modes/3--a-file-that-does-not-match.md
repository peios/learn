---
title: A File That Does Not Match
description: A file whose hash differs from the one recorded at install — what that can mean, how to tell the cases apart, and reinstalling.
---

`peipkg verify` reports an installed file whose content no longer
matches the hash recorded at install.

## What it can mean

**A legitimate edit.** Someone changed a configuration file, or patched
a binary in place.

**Corruption.** Storage failure, or a rollback that did not complete
(§14.2).

**Tampering.** Something modified an installed file.

**Neither, for a preserved configuration file.** An upgrade that
preserved an operator's edit records the *new* version's hash against
the original path while leaving the operator's content there. That file
is reported as modified on every run afterwards, permanently, and
nothing about it is wrong (§6.2).

## Distinguishing them

The fourth case is identifiable: a file under a configuration path with
a `.peipkg-new` sibling is a preserved edit, and the sibling holds what
the package shipped.

For the rest, the recorded hash is what the package's files manifest
said at install, so re-downloading the package and comparing is
conclusive about what the content should be.

## Reinstalling

There is no reinstall verb. Restoring a file to what its package shipped
means removing the package and installing it again, in two transactions,
or downgrading and upgrading across the same version.

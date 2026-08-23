---
title: Reverting a Version
description: Reverting to an earlier version is an ordinary downgrade through the ordinary machinery — its procedure, constraints and scope.
---

Reverting an installed package to an earlier version is an ordinary
downgrade, and runs through the ordinary transaction machinery with the
ordinary guarantees.

## The procedure

1. Query the archive index for the available versions of the package.
2. Select the desired one.
3. Run an upgrade with that version as the new version, which requires
   explicit downgrade authorisation (§6.5).

## Constraints

The target has to be available from a configured repository's archive
index, or already cached locally. A version pruned from the archive
cannot be reached without an externally supplied package file.

Reverting may require adjusting dependents whose constraints the older
version does not satisfy. The resolver determines that, and the plan may
include further downgrades or removals.

## Scope

Reverting a package's version reverts that package's payload and nothing
else. Registry state, configuration materialised by reconcillers,
runtime data under `/var/`, and user data are unaffected.

> [!NOTE]
> Comprehensive system rollback, including state under registry control,
> is a higher-level concern handled by recovery snapshots and other
> mechanisms outside the package manager. Package-level version reversion
> covers the common case of "this update broke something; put it back".

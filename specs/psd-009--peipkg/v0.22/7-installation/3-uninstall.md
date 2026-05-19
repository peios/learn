---
title: Uninstall
---

This section defines the uninstall operation: the
procedure for removing a package from the system.

## Preconditions

An uninstall operation begins with the following inputs:

- The name of the package to uninstall.
- The current installed-package database state.
- The current resolution plan.

The following preconditions MUST hold:

1. The named package is currently installed.
2. No other installed package depends on this package
   (per §4.1) unless the resolution plan includes their
   uninstall as well.
3. No other installed package's `replaces` (§4.1.5)
   target is this package.

If installed dependents block the uninstall, the package
manager MUST either:

- Cascade: include the dependents in the same uninstall
  transaction (per §4.2.7), with explicit user
  authorisation, or
- Refuse: report which dependents block the uninstall and
  abort.

The choice between cascade and refuse is per-transaction
policy.

## Procedure

### Step 1: enumerate

1. Read the package's file list from the package database.
2. Compute the set of paths to remove.
3. Compute the set of side effects to invoke (typically
   ldconfig if the package owned shared libraries,
   depmod if it owned kernel modules, mandb if it owned
   man pages).

### Step 2: prepare

1. For each path to remove, check that the path on disk
   has not been modified by an unowned process. The check
   is content-hash comparison against the hash recorded
   in the package database (extracted from the package's
   `files.json` at install).
2. Files whose on-disk content differs from the recorded
   hash are *modified files*. The package manager MUST
   surface these to the user before removal.
3. The user MAY authorise removal of modified files,
   skip-removal, or abort the uninstall.

> [!INFORMATIVE]
> Modified files indicate either user customisation that
> would be destroyed by removal, or unauthorised
> modification of a system file. Either is worth
> surfacing.

> [!INFORMATIVE]
> Mass-hashing every installed file at uninstall can be
> expensive for large packages (a 1 GB package on
> spinning disk takes seconds). An implementation MAY
> restrict the modification check to files in policy-
> defined paths (typically `/etc/` and locations where
> user customisation is expected) and skip the check for
> binaries, libraries, and other paths not normally
> modified post-install. The decision is operationally
> defined; the format does not require comprehensive
> hashing of every payload file.

### Step 3: remove

For each path to remove:

1. Rename the path aside as a backup (§7.5.1.3) rather
   than deleting it outright, so the uninstall can be
   rolled back and remains undoable (§7.5.2). The backup
   is discarded once the transaction commits and any
   retention window expires.
2. If the path's parent directory is now empty AND the
   parent directory is not owned by another installed
   package, schedule the parent for removal.

After all package-owned paths are processed, remove the
scheduled empty directories in deepest-first order.

### Step 4: side effects

Schedule the side effects identified in step 1 for
invocation at transaction commit. Side effects are
deduplicated and batched per §7.4.6.

### Step 5: deregister

Remove the package's record from the package database.

## File ownership and overlap

A path that is part of multiple installed packages is
not permitted (§3.4.10). However, in degraded scenarios
(database corruption, manual intervention), the package
manager MAY encounter such a state.

If a path scheduled for removal is owned by another
installed package per the database, the package manager
MUST NOT remove the file. The package manager SHOULD
surface the overlap as a database-integrity warning.

## Removal of system-critical packages

Some packages are *system-critical*: their files are
required for the package manager itself, or for core
system function, to work (the package manager binary and
its trust anchors, core system packages). The set is
operationally defined and not specified normatively here.

A package manager MUST refuse to uninstall a
system-critical package unless the operator supplies an
explicit, operation-specific override (for example an
`--allow-critical` flag). This is a foot-gun guard, not a
security boundary: under Peios's access model the operator
already holds whatever authority the underlying file
deletions require (§7.6), so the guard exists to prevent
an accidental `uninstall` from disabling the system — not
to deny an authorised operator who genuinely intends the
removal.

## Side-effect timing on uninstall

Side effects are invoked at transaction commit, after
all packages in the transaction have been removed. The
same deduplication and batching rules as for install
(§7.1.3) apply.

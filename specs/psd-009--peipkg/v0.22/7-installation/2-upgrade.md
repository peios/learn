---
title: Upgrade
---

This section defines the upgrade operation: the procedure
for replacing an installed version of a package with a
different version.

Upgrade is conceptually a single atomic operation
combining an install of the new version and an uninstall
of the old version, with the property that no point in
time leaves the system without the package's content
available.

The same procedure handles upgrades (newer version
replacing older) and downgrades (older version replacing
newer). The two cases differ only in which version
comparison applies; the format treats both identically.

## Preconditions

An upgrade operation begins with the following inputs:

- The new version's `.peipkg` file (already fetched).
- The currently-installed version of the same package.
- The repository the new version was fetched from.
- The current resolution plan.

The following preconditions MUST hold:

1. All preconditions of install (§7.1.1) hold for the new
   version, except the "not already installed" check
   which is replaced by "the currently-installed version
   has the same name and architecture but a different
   version".
2. The new version's dependencies are satisfied (or will
   be satisfied by the in-flight transaction's other
   operations).
3. No package depends on the currently-installed version
   in a way that the new version cannot satisfy.
4. If the new version is older than the currently-
   installed version (downgrade), the user has explicitly
   authorised the downgrade.

## File diff

An upgrade is computed as a diff between the old version's
file set and the new version's file set:

- **Files in old but not in new**: REMOVED at upgrade
  commit.
- **Files in both old and new with identical content
  hash**: untouched.
- **Files in both old and new with different content
  hash**: REPLACED.
- **Files in new but not in old**: ADDED at upgrade
  commit.

Files in `/etc/` are handled by modified-detection. For a
REPLACED `/etc/` file, the package manager compares the
file's current on-disk content hash against the hash
recorded for that file at install:

- **Unmodified** — the on-disk content matches the
  recorded hash: the file is replaced with the new
  version's content, like any other REPLACED file.
- **Modified** — the on-disk content differs: the
  operator's file MUST be left in place; the new
  version's default is written alongside it as
  `<name>.peipkg-new`, and the divergence MUST be
  surfaced in the operation report.

> [!INFORMATIVE]
> The intended end state is the one §3.4.4 describes:
> runtime configuration is materialised by reconciller
> daemons from registry state, operators do not edit
> `/etc/` by hand, and an upgrade replaces seed
> configuration unconditionally. Until the reconciller
> framework exists, modified-detection prevents an
> upgrade from destroying a hand-edited `/etc/` file.
> The models converge: once reconcillers claim a set of
> `/etc/` paths, the package manager applies
> modified-detection only to the unclaimed remainder and
> replaces reconciller-managed seed files unconditionally.

## Procedure

The upgrade procedure consists of the following ordered
steps:

### Step 1: parse and validate

Identical to install step 1 (§7.1.2.1) for the new
version's package.

### Step 2: prepare diff

1. Read the currently-installed version's file list from
   the package database.
2. Read the new version's file list from the new
   `.peipkg`'s `files.json`.
3. Compute the diff (§7.2.2).
4. Verify disk space per §7.1.2.2 step 2 — the staged
   ADDED and REPLACED content. Backups of REPLACED and
   REMOVED files are made by renaming the old files
   aside (§7.5.1.3) and cost no additional space.
5. Verify no ADDED path collides with a path owned by a
   different package than the one being upgraded.

### Step 3: stage replacement

For each REPLACED or ADDED file:

1. Extract from the new `.peipkg` to a temporary file
   **within the destination's own directory**, so the
   commit-time rename is intra-directory and cannot fail
   with `EXDEV` (§7.1.2.3).
2. Verify content hash against `files.json`.

Staged files are named so as not to collide with payload
entries, and are not visible as installed content until
commit, when an atomic rename moves each into place.

### Step 4: apply diff

At transaction commit (§7.4):

1. For each ADDED file: rename the staged file into place
   at the install path (§7.1.2.3) and apply its SD per
   §3.4.7.
2. For each REPLACED file: rename the existing file aside
   as a backup (§7.5.1.3), then rename the staged file
   into place; apply the new file's SD per §3.4.7.
3. For each REMOVED file: rename the file aside as a
   backup (§7.5.1.3). The backup is discarded once the
   transaction commits and any retention window expires.
4. Remove empty directories that are no longer owned by
   any installed package.

### Step 5: side effects

Side effects declared by the new version are scheduled
for invocation at transaction commit. Side effects are
also scheduled if files were REMOVED whose absence
affects the side-effect target (e.g., removing a shared
library requires `ldconfig`, removing a kernel module
requires `depmod`).

A package manager MAY infer additional side-effect
invocations from REMOVED files even if the new package
does not explicitly declare them.

### Step 6: update registration

Replace the package database's record for this package
with the new version's identity, file list, and manifest
contents. The database update is part of the transaction.

## Replaces relations

An upgrade triggered by a `replaces` relation (§4.1.5)
follows the same procedure with the replaced package
treated as the "currently installed version", even though
its name differs from the new package's name.

The package database's record for the replaced package is
removed; a new record for the replacing package is
created. From the system's perspective, the replaced
package is uninstalled and the replacing package is
installed; the diff procedure ensures no payload files
are spuriously removed during the transition.

## Downgrade

A downgrade is an upgrade where the new version is older
than the installed version per §2.2.6. The procedure is
identical to upgrade, with one additional precondition:
the user MUST have explicitly authorised the downgrade.

> [!INFORMATIVE]
> Explicit authorisation is required because downgrades
> are unusual: a downgrade implies the user wants to
> revert to a known-good earlier state, often after a
> failed upgrade. The package manager makes the user
> opt in to ensure the downgrade is intentional rather
> than the result of misconfigured constraints.

## Concurrent dependent updates

If an upgrade in progress would temporarily violate a
dependent package's dependencies (because the new version
is incompatible with the dependent), the resolution plan
MUST include the dependent's upgrade in the same
transaction.

The upgrade procedure MUST NOT be invoked on a single
package without ensuring that any dependents whose
constraints are not satisfied by the new version are also
upgraded (or removed) in the same transaction.

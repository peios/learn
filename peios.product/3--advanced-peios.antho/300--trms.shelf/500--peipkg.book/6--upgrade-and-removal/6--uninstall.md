---
title: Uninstall
description: The preconditions and steps of a removal, what happens to directories, and how overlapping ownership is handled.
---

## Preconditions

The named package is installed; no other installed package depends on it
unless the plan removes them too; and no other installed package's
`replaces` targets it.

Blocked removals cascade or refuse, per §4.6.

## The steps

1. **Enumerate** the package's owned paths from the database.
2. **Check** each non-directory path: that no other installed package
   also owns it (below), and — for a configuration file — that its
   content still matches the hash recorded at install (§6.7). A
   modified configuration file is put to the operator before anything
   is touched.
3. **Prepare** the removal.
4. **Remove**: rename each path aside as a backup rather than deleting
   it, so that the uninstall can be rolled back.
5. **Schedule side effects** implied by what was removed.
6. **Deregister**: delete the package's record, withdraw any role it
   held, and reconcile any role whose claim paths it declared (§9.7).
7. **Reclaim** the directories the package owned that are now owned by
   no package and are empty, deepest first.

Backups are discarded when the transaction commits, except the backup
of a modified configuration file whose removal the operator authorised:
that one is kept beside where the file was.

## Modified configuration files

A configuration file — a path under `/usr/etc/` or the legacy `/etc/`,
the same scope the upgrade's modified-detection uses (§6.2) — whose
content differs from the recorded hash is surfaced before the removal
is prepared, and the operator chooses per file: **remove** it, with the
previous content kept at the backup path and the authorisation written
to the audit stream; **keep** it, in which case it stays where it is
and becomes unowned, since the package's ownership row goes with the
package; or **abort** the transaction. Anything but an explicit remove
or keep aborts, end-of-input included, so `--yes` does not answer the
question and a non-interactive uninstall of a package with a modified
configuration file refuses, naming the file. Binaries, libraries and
data are not hashed at uninstall.

## Directories

Removing the package's rows releases its ownership of its directories.
After the commit, each such directory that no installed package owns
any longer and that is empty is removed, deepest first, so a directory
is attempted after everything it contained. A directory another
package still owns, or that holds anything — an unowned file a runtime
wrote, an operator's addition — is left where it is, silently: those
are reasons to keep it, not failures. Only an unexpected error in
removing an empty unowned directory is reported, as a warning on the
operation report; the transaction has already committed.

An upgrade applies the same rule to the directories the previous
version owned that the new payload does not carry (§6.1).

## Overlapping ownership

Two packages owning one non-directory path is prevented by the database
schema, but a degraded state — a corrupted database, a manual
intervention — could produce one. Each non-directory path scheduled
for removal is checked against the ownership table first. A path that
another installed package also owns is left in place, since the other
owner still needs it, and the operation report carries a
database-integrity warning naming the path and both owners, so that the
operator knows the database needs inspection rather than the
filesystem.

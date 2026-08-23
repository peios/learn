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
2. **Prepare** the removal.
3. **Remove**: rename each path aside as a backup rather than deleting
   it, so that the uninstall can be rolled back.
4. **Schedule side effects** implied by what was removed.
5. **Deregister**: delete the package's record, withdraw any role it
   held, and reconcile any role whose claim paths it declared (§9.7).

Backups are discarded when the transaction commits.

## Directories

Directory entries are skipped. A package's directories are left in
place, and its removal leaves the skeleton behind.

Because deleting the package's rows removes its ownership of those
directories, they become owned by nothing, and no later operation
reclaims them.

## Overlapping ownership

Two packages owning one non-directory path is prevented by the database
schema, but a degraded state — a corrupted database, a manual
intervention — could produce one. peipkg does not check for it during
removal, and does not surface it as a database-integrity warning.

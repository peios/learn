---
title: The Journal
description: The journal is rows in the package database rather than a separate file — what it holds, its integrity, attribution and versioning.
---

The transaction journal is **part of the package database**. A pending
transaction is rows in the database store, not a separate file with a
separate format.

## What it holds

| Row kind | Content |
|---|---|
| Transaction | Identifier, state, schema version, and for a cross-root operation the shared cross-root identifier |
| Operation | One per package operation: kind, package, root |
| File | One per file operation: final path, staged path, backup path, action |
| Directory | One per directory the transaction created, so rollback can remove it |
| Commit payload | For a cross-root transaction, the state a roll-forward would need |

Recording intent and committing are ordinary database writes, and the
journal inherits the database's transactional guarantees.

## Integrity

The database is stored under a security descriptor granting write access
to the tier of principals permitted to install packages. That descriptor
is the journal's integrity protection: a principal outside the tier
cannot forge an entry, and one inside it already holds installation
authority, so a write from within is not an escalation.

The staging area is under the same descriptor.

## Attribution

Claim link operations do not have an operation row of their own within
an install. They are appended to the last staged package operation as a
carrier, so the file rows recording a claim link change are attributed
to whichever package sorted last. A standalone grant or revoke uses a
synthetic operation named for the role, and is attributed correctly.

The consequence is confined to history display; recovery is
action-agnostic and unaffected.

## Versioning

Each transaction records the journal schema version it was written
under. A peipkg version that can read that schema recovers the
transaction directly; one that cannot refuses, with an error naming the
schema version rather than a generic failure.

That is what makes upgrading peipkg itself unremarkable (§8.5): the
binary running the next recovery may be a different version from the one
that started the transaction, and the version stamp is how it knows
whether it can.

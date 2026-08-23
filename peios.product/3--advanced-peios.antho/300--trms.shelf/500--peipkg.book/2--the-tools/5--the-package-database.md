---
title: The Package Database
description: peipkg's entire persistent state is one transactional store — why that choice is load-bearing, what it holds, and how it is protected.
---

peipkg's entire persistent state is one database. It is a transactional
store — SQLite in write-ahead-logging mode — and that choice is
load-bearing rather than incidental.

## Why it is a real database

Three of this manual's guarantees rest on it.

**The commit is atomic.** A transaction's new installed state and the
closing of its journal entry are written in one database transaction, so
the transaction is committed or it is not. There is no window in which
it is partly committed, which is why recovery never has to finish a
half-done commit (§7.8).

**Reads see a consistent snapshot.** A query beginning at some moment
sees committed state as of that moment, regardless of a write committing
underneath it. This is what lets a read-only query run without taking
the transaction lock at all.

**Constraints are enforced by the schema.** The rule that two packages
cannot own the same non-directory path is a partial unique index, not
an application check — so it holds even against a code path that forgot
to look.

peipkg refuses to open a database that is not in write-ahead-logging
mode, rather than proceeding with weaker guarantees than it documents.

## What it holds

| Content | Purpose |
|---|---|
| Installed packages | Name, version, architecture, originating repository, install time, and the stored manifest |
| Owned files | One row per path a package owns, with its type and the hash recorded at install |
| Repositories | Base URL, trust keys with their statuses, priority, signature policy, and the recorded freshness floor |
| Role holders | Which package holds each role |
| Claim links | Which links have been materialised, and for which role and slot |
| Transactions | The journal: pending and completed transactions, their operations, and the backup map |
| Machine metadata | The system's primary architecture, and the registered installation roots |

The journal is rows in this database rather than a separate file with a
separate format. Recording intent and committing are ordinary database
writes, and the journal inherits the database's transactional
guarantees.

## Protection

The database is stored under a security descriptor granting write access
to the tier of principals permitted to install packages on the system.
That descriptor is the journal's integrity protection: a principal
outside the tier cannot forge a journal entry, and a principal inside it
already holds installation authority, so a write from within is not an
escalation.

The staging area is stored under the same descriptor.

> [!NOTE]
> An earlier design signed each commit record with a key bound to a
> dedicated package-manager principal. peipkg holds no principal of its
> own (§13.1), so there is no key to sign with; the descriptor on the
> database is the protection instead. Narrowing that descriptor so the
> journal is writable only *through* the package-manager executable
> becomes possible once an elevated-executable mechanism exists, and
> would be a tightening rather than a correction.

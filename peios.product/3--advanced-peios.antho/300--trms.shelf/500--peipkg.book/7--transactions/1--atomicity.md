---
title: Atomicity
description: Distinguish each root's package-database durability boundary from filesystem visibility and coordinated cross-root recovery.
---

Package transactions coordinate recorded package state and changes to files.
That does not make all filesystem changes, every root's database, and
post-commit maintenance one instantaneous switch.

For the cross-root path reviewed in peipkg `8b588ae8`:

- Packages for all participants are fetched and verified before extraction.
- Preparing roots persists recovery data and moves files into place. Those
  files can become visible before a root's package-state commit.
- Package state commits separately in each root. A commit failure can leave
  some roots committed and others pending; already committed roots are not
  undone by rolling back a sibling.
- A preparation rollback can itself fail, leaving a pending journal and
  files that must not be treated as restored.

These boundaries follow the
[coordinated execution sequence](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L230-L348),
[preparation and per-root commit](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L554-L655),
and [rollback-error handling](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L668-L724).
Logical errors, power loss or other system faults therefore require checking
the actual journal and files. The older blanket promises that uncommitted
work is invisible and partial effects never occur do not describe this path.

## The single durability boundary

Within **one root**, updating package metadata and closing that root's
journal transaction share a single database transaction. Its database commit
is that root's durability boundary. It is not a global cross-root commit.

A pending cross-root journal does not by itself determine recovery direction:
if none of the participants committed, recovery rolls pending work back;
after a participant commits, recovery rolls pending siblings forward using
persisted completion data. Missing data or another failure can prevent
completion. See [Crash recovery](~peios/peipkg/transactions/crash-recovery#cross-root-the-exception).

The source qualification here does not verify every single-root failure
path or the revision shipped in an installed image. Use the
[operator recovery checks](~peios/package-management/transactions-and-recovery)
and [visibility limits](~peios/peipkg/transactions/visibility) before treating
a failed or interrupted operation as unchanged, restored or ready to use.

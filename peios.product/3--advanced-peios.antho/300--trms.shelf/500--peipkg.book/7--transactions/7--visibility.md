---
title: Visibility
description: Queries see only committed transactions under snapshot isolation, and the one place that boundary is softer.
---

The database state visible to a query reflects only committed
transactions.

Reads are snapshot-isolated: a query beginning at some moment sees a
consistent view of committed state as of that moment, regardless of a
write transaction committing while it runs. This is a property of the
store rather than of peipkg's use of it, and it is why a read-only query
needs no lock.

Committed package metadata is not the same as filesystem or journal
visibility. A pending journal is evidence of work in progress, and staged
files move to their final paths during application. In the reviewed
cross-root path, [preparation persists recovery data and applies file moves](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L554-L596)
before the per-root package-state commits. Outside processes can therefore
observe files from a transaction whose package metadata has not committed.

peipkg does inspect its own uncommitted state — verifying a staged file,
computing what remains to apply — which is not a visibility leak.

## Where the boundary is softer

Several things about an in-flight transaction are observable from outside.

Staged files and backups are siblings of their destinations rather than
files in a private directory, so they are visible in a directory
listing under names carrying the transaction identifier. They are not at
the paths anything would look them up by, but they are there.

And within the apply phase, a file is momentarily absent between its
original being renamed aside and its replacement being renamed in.
Anything opening that exact path in that window sees nothing.

Across roots, [commits and post-commit maintenance happen root by root](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L599-L655).
A snapshot of one database does not prove the state of every participant or
which binaries a running process has mapped. See
[Atomicity](~peios/peipkg/transactions/atomicity) and the
[operator recovery checks](~peios/package-management/transactions-and-recovery#across-more-than-one-root).
These cross-root observations are pinned to peipkg `8b588ae8`, not a runtime
test or a guarantee about every shipped revision.

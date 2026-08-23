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

In-progress state is not visible outside peipkg's own process. Staged
files do not appear at their final install paths until the apply phase,
and journal rows describe a transaction that queries do not see.

peipkg does inspect its own uncommitted state — verifying a staged file,
computing what remains to apply — which is not a visibility leak.

## Where the boundary is softer

Two things about an in-flight transaction are observable from outside.

Staged files and backups are siblings of their destinations rather than
files in a private directory, so they are visible in a directory
listing under names carrying the transaction identifier. They are not at
the paths anything would look them up by, but they are there.

And within the apply phase, a file is momentarily absent between its
original being renamed aside and its replacement being renamed in.
Anything opening that exact path in that window sees nothing.

---
title: The Lock
description: At most one transaction per root at a time — how the exclusive lock is acquired, why staleness cannot happen, and what it does not cover.
---

At most one transaction is in progress at a time in a given root.

peipkg acquires an exclusive lock before beginning. A second invocation
detects the lock and fails immediately with a "transaction in progress"
message rather than waiting.

## Staleness cannot happen

The lock is a `flock(2)` advisory lock on a file in the root's state
directory, held by the running process. The kernel releases it when the
process exits, however it exits — cleanly, by signal, or by being
killed.

That makes staleness impossible by construction. There is no timeout, no
liveness probe, and no process-identity comparison, because there is
nothing that could hold a lock after the holder is gone.

> [!NOTE]
> The alternative — a lock file with a recorded process identifier, a
> `kill(pid, 0) == ESRCH` liveness probe, and a timeout — is the design
> this avoids. A timeout-only staleness check
> breaks single-writer atomicity outright: a long-running but perfectly
> live transaction, a fifty-package install on slow storage, can be
> declared dead by another invocation, and both then proceed
> concurrently. An advisory lock is not a weaker version of that design;
> it is a stronger one.

A second structural guard backs it up: the database carries a partial
unique index permitting at most one transaction in the pending state, so
even a defect that bypassed the lock could not produce two concurrent
pending transactions.

## What the lock does not cover

A read-only query against committed state does not take the lock. The
database provides snapshot-isolated reads, so a query sees a consistent
view of committed state as of the moment it began, regardless of a write
committing underneath it. Listing installed packages during a long
install is safe and does not block.

---
title: Crash Recovery
description: peipkg checks the journal before permitting new work — why it rolls back rather than forward, and the cross-root exception.
---

Before permitting new work, peipkg checks the journal for a pending
transaction.

- **No pending transaction** — nothing to do.
- **A pending transaction** — roll it back. Restore every displaced
  original from the backup map, remove the directories the transaction
  created, discard its staged files, and clear it from the journal.

Recovery is itself crash-safe: every action it takes is a rename from
the backup map, and every step checks the current state before acting,
so re-running after an interruption converges on the same result.

## Rollback rather than roll-forward

For a single-root transaction there is no roll-forward. Because the
database commit is the single durability boundary and is itself atomic,
a recovered transaction is only ever committed — in which case the
database says so and there is nothing to recover — or pending, in which
case it rolls back.

> [!NOTE]
> Roll-back-only recovery is possible *because* the database is a
> transactional store. A design that applies file changes after a
> separate commit-intent record needs roll-forward to finish what that
> record promised. Here the database commit and the fact that the
> transaction is done are the same atomic event, so there is nothing
> left to finish.

## Cross-root: the exception

A cross-root operation commits one root at a time. Once a root has
committed, its transaction is done and cannot be undone by rolling back
a sibling.

In [peipkg `8b588ae8`'s coordinated recovery](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L805-L917),
pending participants roll back if none committed. If a sibling has committed,
recovery completes pending participants from persisted completion data
instead. Missing or malformed data needed for roll-forward causes refusal.
Recovery can itself fail after another participant has been reconciled.

Keep the named-root topology intact and make every participant reachable
from the same anchor used for the operation. The
[CLI's reachable-root scan](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/recover.go#L12-L119)
does not establish that absent or unregistered participants are detected.
Its `rolled back cross-root transaction` message also covers successful
roll-forward; inspect per-root history instead of treating that phrase as
the recovery direction.

The [roll-forward path](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L773-L802)
applies persisted database metadata and attempts backup cleanup. It does not
invoke the normal post-commit side-effect runner. The
[operator recovery checks](~peios/package-management/transactions-and-recovery#across-more-than-one-root)
cover verification and the remaining maintenance work. These statements are
pinned to source, not a runtime test or a guarantee about every released image.

## When it runs

Recovery runs at the head of every install, upgrade, and uninstall,
before the requested work begins and under the lock. It is not something
an operator invokes; `peipkg recover` exists, but the ordinary path is
automatic.

A pending cross-root transaction discovered by a single-root operation
is refused rather than recovered, and blocks all further work in that
root until `peipkg recover` is run.

Automatic recovery emits no audit event. The `recover` command does, so
a rollback recovered by the next ordinary install leaves no record in
the audit stream while the same rollback performed deliberately does.

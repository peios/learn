---
title: Transaction Semantics
---

Transactions provide atomic multi-key writes within a single source.
A process groups registry operations into a transaction -- either all
operations commit together or none do. This is the mechanism for
consistent configuration updates: a role installation writes service
definitions, default config, and registry entries as a single atomic
unit.

## Scope

**Hive-scoped.** A transaction binds to a specific hive on its
first mutating operation (value write, key create, key delete,
key hide, SD change, blanket tombstone). Read operations within
a transaction do NOT bind it. All subsequent operations MUST
target keys in the same hive. An operation targeting a different
hive fails with EXDEV. LCS enforces hive-scoping before
forwarding operations to the source -- sources never receive
cross-hive operations within a transaction.

Cross-source atomicity would require two-phase commit and is not
supported.

## Lifetime

A transaction exists for the lifetime of its fd (returned by
reg_begin_transaction). Three ways a transaction ends:

- **Commit.** REG_IOC_COMMIT on the transaction fd. The source
  atomically applies all operations. Watch events fire. The fd
  SHOULD be closed after commit. Further operations on a committed
  transaction fd return EINVAL.

- **Explicit abort.** close() on the transaction fd without
  committing. The source discards all pending operations. No watch
  events are generated.

- **Implicit abort.** Process death closes the fd, which aborts.
  No orphaned transactions.

## Timeout

LCS starts a timer when the transaction fd is created. If the
transaction is not committed or aborted within the timeout, LCS
auto-aborts it (sends RSI_ABORT_TRANSACTION to the source and
closes the transaction fd).

This prevents a stalled or malicious process from holding the
source's write lock indefinitely. Because sources like loregd
serialise writers via SQLite WAL, a stalled transaction blocks all
other registry writes to that source.

The timeout is configurable via the self-configuration mechanism
(default 30 seconds). See §8.2.

## Isolation

**Read-your-own-writes.** Within a transaction, reads see the
transaction's own uncommitted writes. This is handled by the
source: when LCS sends a read with a txn_id, the source reads
from within its open transaction, which naturally includes pending
writes. LCS does not cache transaction state in the kernel.

**External isolation.** Other threads and processes see committed
state only. A transaction's writes are invisible to external
readers until commit.

**Layer precedence coherency.** If a transaction modifies layer
precedence (by writing to `Machine\System\Registry\Layers\`), the
new precedence does NOT take effect within the transaction. LCS
resolves layers using its in-memory precedence cache, which is
updated only at commit time via the self-watch mechanism. Within
the transaction, layer resolution uses the pre-transaction
precedence. Reading back the precedence value itself shows the new
value (read-your-own-writes from the source), but resolution of
other values uses the old order.

## Conflict handling

Transactions are atomic but not conflict-detecting at the key
level. If two transactions write to the same value, both commits
succeed -- the last to commit wins (its write has the higher
sequence number).

Write serialisation is the source's responsibility. Sources MUST
serialise concurrent commits. For loregd, SQLite's WAL mode
serialises writers at the database level. A second writer blocks
until the first commits or the transaction timeout fires.

The RSI contract requires: commits are atomic (all-or-nothing),
writes within a transaction are ordered, and concurrent commits
are serialised. Key-level conflict detection is not required.

**Write starvation.** Because writers are serialised, a
long-running transaction can block other writers. The transaction
timeout bounds the maximum starvation window.

## Watch interaction

Watch events fire at commit time, not during individual operations
within the transaction. Watchers never see intermediate
transactional states.

All changes within a committed transaction generate their events
as a batch, ordered by the sequence in which operations were
performed. No interleaving with events from other operations
between batch members.

Aborted transactions generate no events.

## Constraints

- **No nesting.** Transactions are flat. No savepoints, no
  sub-transactions.

- **No cross-source.** Transactions MUST NOT span sources.

- **One active transaction per fd.** A process can have multiple
  concurrent transactions (multiple transaction fds), but each fd
  represents exactly one transaction.

- **Per-source bound transaction limit.** LCS enforces a
  system-wide maximum number of concurrently bound transactions
  per source. A transaction becomes bound on its first mutating
  operation. If the limit is reached, subsequent operations that
  would bind a new transaction to that source return EBUSY. The
  limit is configurable via the self-configuration mechanism
  (MaxBoundTransactionsPerSource, default 16). This prevents
  transaction chaining attacks where colluding processes hold the
  source's write lock indefinitely by serially binding
  transactions at the timeout boundary.

- **Reads are permitted.** Transactions are not write-only. Reads
  within a transaction see the transaction's uncommitted state,
  which is useful for verify-then-write patterns.

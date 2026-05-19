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

Transaction creation is source-agnostic. reg_begin_transaction()
does not choose a source and therefore cannot fail because a
particular source lacks transaction support. If the first operation
that would bind the transaction targets a source that does not
support explicit transactions, that operation fails with ENOTSUP and
the transaction remains unbound.

If a source is Down before first bind, the attempted binding
operation fails according to normal source-unavailable rules and the
transaction remains unbound. If a source goes Down after a
transaction is bound, the transaction object enters SOURCE_DOWN as
described in §10.1.

Reads with an unbound transaction fd behave as ordinary
non-transactional reads. They do not bind the transaction and LCS
sends them to the source with txn_id = 0. After a transaction is
bound by a mutating operation, reads against the same hive/source use
the transaction context and are sent with the transaction ID,
providing read-your-own-writes. Reads against a different hive/source
than the bound transaction fail with EXDEV. Reads using a committed,
aborted, or otherwise closed transaction object fail with EINVAL.
Reads using a timed-out transaction object fail with ETIMEDOUT.
Reads using a transaction object whose bound source went Down fail
with EIO.

Cross-source atomicity would require two-phase commit and is not
supported.

## Lifetime

A transaction object is represented by the fd returned by
reg_begin_transaction(). It remains addressable until the fd is
closed, even after it reaches a terminal state. Four ways a
transaction reaches a terminal state:

- **Commit.** REG_IOC_COMMIT on the transaction fd. The source
  atomically applies all operations. Watch events fire. The
  transaction object enters the COMMITTED terminal state. The fd
  SHOULD be closed after commit. Further mutating or read operations
  using the committed transaction fd return EINVAL.

- **Explicit abort.** close() on the transaction fd without
  committing. The source discards all pending operations. The
  transaction object enters the ABORTED terminal state during fd
  release. No watch events are generated.

- **Implicit abort.** Process death closes the fd, which aborts.
  The transaction object enters the ABORTED terminal state during fd
  release. No orphaned transactions.

- **Timeout abort.** The transaction lifetime timer fires. LCS marks
  the transaction object TIMED_OUT and aborts it as described below.
  The fd remains present in the caller's fd table until normal fd
  close. Further mutating or read operations using the timed-out
  transaction fd return ETIMEDOUT.

Transaction fds are pollable. When a transaction reaches any terminal
state, LCS wakes poll waiters and reports POLLERR | POLLHUP. Callers
that need a race-free reason for wakeup query REG_IOC_TXN_STATUS on
the transaction fd.

## Timeout

LCS starts a timer when the transaction fd is created. If the
transaction is not committed or aborted within the timeout, LCS
auto-aborts it. The transaction object is marked TIMED_OUT, poll
waiters are woken, and future operations using the transaction fd
return ETIMEDOUT. If the transaction was bound and no commit is
already in flight, LCS sends RSI_ABORT_TRANSACTION to the source.
The fd is not forcibly removed from the caller's fd table; normal
close still releases it.

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
writes. LCS does not cache uncommitted registry data in the kernel
for read resolution.

LCS does maintain a bounded transaction mutation log for
kernel-owned semantics. Each mutating operation accepted into a
transaction records enough metadata for LCS to compute affected
keys, values, layer names, sequence numbers, hive generation
updates, and watch events after a successful commit. This log is not
the source of truth for reads or rollback; source transaction state
remains authoritative for uncommitted data.

If LCS cannot allocate the mutation-log entry for a transactional
operation, the operation fails before it is sent to the source. On
explicit abort, transaction lifetime timeout before commit dispatch,
source-down cancellation, a late commit error after a retained
post-dispatch timeout, or source connection teardown while a
post-dispatch commit response is retained, LCS discards or releases
the mutation log and emits no normal watch events for the
transaction. On successful commit, LCS uses the mutation log and
source queries as needed to compute effective-state changes and emit
watch events.

If REG_IOC_COMMIT returns EBUSY or a synchronous EIO before the
transaction reaches a terminal state, the transaction remains
ACTIVE_BOUND. LCS MUST retain the mutation log, MUST NOT emit normal
watch events, and MUST NOT report terminal poll wakeups for that
failed commit attempt. The caller may retry REG_IOC_COMMIT or close
the transaction fd to abort.

If a transaction commit request times out after dispatch at the RSI
request layer, LCS MUST retain the transaction mutation log until the
late commit response is processed or the source connection is torn
down. A late successful commit uses the retained log to produce the
same generation updates and watch events as an on-time commit. A late
commit error releases the log without normal watch events.

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

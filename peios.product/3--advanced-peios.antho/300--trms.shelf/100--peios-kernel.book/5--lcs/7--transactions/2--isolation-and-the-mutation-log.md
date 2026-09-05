---
title: Isolation and the Mutation Log
description: Read-your-own-writes inside a transaction, implemented by the source rather than LCS — the mutation log, sequence numbers and conflicts.
---

## Read-your-own-writes

Within a bound transaction, reads see the transaction's own uncommitted
writes. [*txn.isolation.read-your-own-writes]
LCS does not implement this; the source does. A read tagged with the
transaction id is executed by the source inside its open transaction,
which naturally includes the pending writes.

No uncommitted registry data is cached in the kernel for the purpose of
resolving reads. [*txn.isolation.no-uncommitted-data-cached-in-the-kernel]

Externally, only committed state is visible. A transaction's writes are
invisible to other threads and processes until commit. [*txn.isolation.uncommitted-writes-are-invisible-externally]

## The mutation log

LCS does keep something: a per-transaction **mutation log**, holding
what the kernel needs to know after a successful commit and cannot ask
the source for afterwards. Each accepted mutating operation records the
affected key, value or layer name, its assigned sequence number, the
ancestor chain for watch dispatch, and enough context to compute
effective-state changes. [*txn.isolation.log-records-per-operation-context]

The log is not the source of truth for reads and it is not a rollback
journal — the source's own transaction state is authoritative for
uncommitted data. [*txn.isolation.log-is-not-a-rollback-journal]
The log exists so that when the source says "yes", LCS can produce the
hive generation updates and the watch events that correspond to what
was just committed.

It is bounded at 4096 entries. That bound is a compile-time constant
rather than one of the self-configuration parameters. [*txn.isolation.log-bounded-at-4096-entries]

Exceeding it fails the operation with `ENOMEM`. [*txn.isolation.log-full-fails-the-operation-with-enomem]

An operation whose log entry cannot be allocated fails **before it is
sent to the source**. [*txn.isolation.log-allocation-failure-precedes-the-source-send]
That ordering is deliberate: an operation the source applied but the
kernel cannot account for is exactly the state the log exists to
prevent.

The log is released, with no events emitted, on explicit abort, on a
lifetime timeout that fires before a commit is dispatched, on
source-down cancellation, on a late commit error, and on source
teardown while a post-dispatch commit response is still retained. [*txn.isolation.log-release-conditions]

It is **retained** across a post-dispatch commit timeout, because the
source may still answer. [*txn.isolation.log-retained-across-a-post-dispatch-timeout]

## Sequence numbers

A transactional mutation is assigned its sequence number when it is
accepted into the transaction, not at commit. [*txn.isolation.sequence-assigned-on-accept-not-at-commit]
This preserves the order in which the caller performed the operations,
which is what layer tiebreaking and watch ordering need.

If the transaction aborts, those numbers are simply never used. [*txn.isolation.aborted-sequence-numbers-are-never-used]
Gaps in the sequence space are normal and mean nothing (§5.3.7).

## Layer precedence coherency

Layer metadata lives in the registry, so a transaction can write to it —
and that raises the question of whether a precedence change takes
effect inside the transaction that made it. It does not. [*txn.isolation.precedence-change-does-not-take-effect-in-its-own-transaction]

Resolution always uses the published layer cache, which is refreshed
only at commit. [*txn.isolation.resolution-uses-the-published-layer-cache]

Reading the `Precedence` value back inside the transaction shows the
new number, because that is an ordinary read-your-own-writes read from
the source. [*txn.isolation.precedence-value-reads-back-as-the-new-number]

Resolving any *other* value in the same transaction still uses the old
precedence order. [*txn.isolation.other-values-resolve-under-the-old-precedence]
The two are consistent with each other and with the rule that a
transaction's effects become real at commit.

The refresh is deferred to commit, dropped on abort, and performed
before `REG_IOC_COMMIT` returns on success. [*txn.isolation.layer-cache-refresh-completes-before-commit-returns]

## Conflicts

Transactions are atomic. They are not conflict-detecting. [*txn.isolation.no-conflict-detection]

If two transactions write the same value, both commits succeed and the
one that committed second wins, because its write carries the higher
sequence number. [*txn.isolation.second-committer-wins]
There is no read set, no version check, and no per-key validation
anywhere in the commit path.

Serialising concurrent writers is the source's responsibility, not
LCS's. The RSI requires only that commits are atomic, that writes
within a transaction are ordered, and that concurrent commits are
serialised. [*txn.isolation.rsi-requires-atomic-ordered-serialised-commits]

Conditional writes are the mechanism for the cases where losing an
update matters. `REG_IOC_SET_VALUE` takes an `expected_sequence`, the
source verifies it atomically against the layer's own entry, and a
mismatch returns `EAGAIN` (§5.5.3).

That is a per-operation check, not a transaction-level one, and it is
deliberately scoped to a single layer: a higher-precedence layer
overriding a value is not a conflict, it is the layer system
working. [*txn.isolation.conditional-write-is-per-operation-and-single-layer]

---
title: Commit and Failure
description: What a commit triggers in order, the failures that leave a transaction open, and what happens when the watch events cannot be delivered.
---

`REG_IOC_COMMIT` marks the transaction as having a commit in flight and
sends `RSI_COMMIT_TRANSACTION`. [*txn.commit.marks-in-flight-and-sends-rsi-commit]
What happens next depends on the answer.

## Success

The source's `RSI_OK` triggers, in order: the layer metadata cache
refresh for any layer names the transaction touched, the hive
generation increment, orphan tracking for keys that lost their last
path entry, and the watch event batch derived from the mutation log. [*txn.commit.post-commit-step-order]

The object then becomes `COMMITTED`, the log is released, poll waiters
are woken, and the ioctl returns 0. [*txn.commit.success-finalises-and-returns-zero]

The hive generation is incremented once per committed transaction per
affected hive, however many operations the transaction contained. [*txn.commit.generation-incremented-once-per-transaction-per-hive]

## Failure that leaves the transaction open

A source that cannot take the write lock answers `RSI_TXN_BUSY`, which
becomes `EBUSY`; a synchronous commit failure becomes `EIO`. [*txn.commit.busy-is-ebusy-and-commit-failure-is-eio]

In both cases the transaction stays `ACTIVE_BOUND`: [*txn.commit.failed-commit-stays-active-bound]

- the mutation log is retained; [*txn.commit.failed-commit-retains-the-log]
- no watch events are emitted; [*txn.commit.failed-commit-emits-no-events]
- poll waiters are **not** woken as though the transaction had become
  terminal. [*txn.commit.failed-commit-does-not-wake-poll-waiters]

The in-flight marker is cleared, so the caller may simply retry
`REG_IOC_COMMIT`, or close the fd to abort. Nothing has been lost. [*txn.commit.in-flight-marker-cleared-so-retry-is-allowed]

## Timeout after dispatch

If the request timeout expires after the commit was dispatched, the
caller receives `ETIMEDOUT` and the object becomes `TIMED_OUT`, but the
mutation log is kept and the request record stays in the source's
in-flight table. The source may still answer. [*txn.commit.post-dispatch-timeout-keeps-log-and-request]

`ETIMEDOUT` on a commit means *may or may not have committed*. A caller
that needs certainty checks state before retrying. [*txn.commit.etimedout-is-indeterminate]

A late `RSI_OK` applies the full set of kernel-side effects from the
retained log — the same generation updates and the same watch events an
on-time commit would have produced. Watchers may therefore observe the
effects of a transaction whose caller was told it timed out. [*txn.commit.late-ok-applies-the-full-effects]

A late error releases the log with no effects. [*txn.commit.late-error-releases-the-log-with-no-effects]

The transaction object does **not** move to `COMMITTED` when a late
success arrives. It stays `TIMED_OUT`, so a caller that queries
`REG_IOC_TXN_STATUS` afterwards is told `TIMED_OUT` with a
`terminal_errno` of `ETIMEDOUT`, even though the writes are durable and
the watch events have gone out. [*txn.commit.late-success-leaves-the-state-timed-out]
The state reflects what the caller was told, not what the source did.

## When the watch events cannot be derived

Two of the post-commit steps query the source. Working out which keys
were orphaned by a key deletion needs a lookup that can only be made
after the commit, and expanding a blanket tombstone into per-value
events needs the value set.

If that derivation cannot complete exactly, LCS does not reinterpret a
successful commit as a failed one and does not emit a partial set of
events. It delivers `OVERFLOW` to the affected watchers instead,
releases the retained replay state, and reports the commit as
successful, which it was. [*txn.commit.underivable-events-become-overflow]

A late response arriving afterwards does not resurrect the individual
events once overflow recovery has been chosen. [*txn.commit.overflow-recovery-is-not-undone-by-a-late-response]

The carve-out is narrower than it might appear. It covers the orphan
lookup and the watch batch. [*txn.commit.carve-out-covers-only-orphan-lookup-and-watch-batch]

The other two post-commit steps — publishing the layer metadata cache
and recording the hive generation — are state updates rather than event
derivation, and a failure in either returns `EIO` and marks the source
Down. [*txn.commit.cache-or-generation-failure-is-eio-and-marks-the-source-down]

## Abort

Aborting generates no events, ever, and releases the log. [*txn.commit.abort-emits-no-events-and-releases-the-log]

The source is told to roll back with `RSI_ABORT_TRANSACTION` if the
transaction was bound. [*txn.commit.abort-sends-rsi-abort-when-bound]

Process death is the same path: closing the fd aborts.

---
title: Scope and Lifetime
description: Grouping registry operations so they commit together or not at all — binding, states, timeout, and sources that do not support them.
---

A transaction groups registry operations so that they commit together
or not at all. Installing a role writes service definitions, defaults
and registry entries; a transaction is what makes that one event rather
than a sequence of partially-applied ones.

`reg_begin_transaction` takes no arguments and returns a transaction
fd. It contacts no source: it allocates an id, creates an anonymous
inode, starts the lifetime timer, and returns. A transaction begins in
the state `REG_TXN_ACTIVE_UNBOUND`.

## Binding

A transaction binds to a source on its first **mutating** operation.
There are seven: writing a value, deleting a value entry, setting or
removing a blanket tombstone, creating a key, deleting a key's path
entry, hiding a key, and changing a Security Descriptor.

Reads never bind. A read passed an unbound transaction fd is sent to
the source with a transaction id of zero and behaves as an ordinary
non-transactional read.

Once bound, every operation on that fd must target the same hive.
One that does not fails with `EXDEV`, and it fails in the kernel,
before anything reaches a source — a source never sees a cross-hive
operation inside a transaction. Cross-source atomicity would require
two-phase commit and is not supported.

Binding identity is the pair of source and hive root GUID carried on
the transaction object, which identifies the hive exactly.

## Sources that do not support transactions

Because `reg_begin_transaction` chooses no source, it cannot fail for
lack of transaction support. The failure surfaces on the operation that
would have bound: LCS sends `RSI_BEGIN_TRANSACTION`, the source answers
`RSI_TXN_NOT_SUPPORTED`, and the operation returns `ENOTSUP`. The
transaction stays `ACTIVE_UNBOUND`, its source binding untouched, and
the caller can use the fd against a different hive.

There is no advance check of whether a source supports transactions.
The answer comes from the source, on the attempt.

If the source is Down before the first bind, the binding operation
fails `EIO` under the ordinary rules and the transaction likewise
remains unbound. If a source goes Down after binding, the transaction
becomes `REG_TXN_SOURCE_DOWN` (§5.8.5).

## States

| State | Value | Meaning |
|---|---|---|
| `REG_TXN_ACTIVE_UNBOUND` | 0 | Active, no source chosen. |
| `REG_TXN_ACTIVE_BOUND` | 1 | Active, bound to a source. |
| `REG_TXN_COMMITTED` | 2 | Commit completed. |
| `REG_TXN_ABORTED` | 3 | Explicitly or implicitly aborted. |
| `REG_TXN_TIMED_OUT` | 4 | The lifetime timer fired. |
| `REG_TXN_SOURCE_DOWN` | 5 | The bound source went Down. |

`REG_IOC_TXN_STATUS` reports the state and a `terminal_errno`: 0 for
`COMMITTED`, `EINVAL` for `ABORTED`, `ETIMEDOUT` for `TIMED_OUT`, `EIO`
for `SOURCE_DOWN`, and 0 while active.

For `COMMITTED`, `terminal_errno` is not the errno that a further
operation would return. A committed transaction reports 0, but using
its fd again returns `EINVAL`.

## Reaching a terminal state

- **Commit.** `REG_IOC_COMMIT` on the transaction fd. The source
  applies everything atomically, watch events fire, and the object
  becomes `COMMITTED`. Later use of the fd returns `EINVAL`. The fd
  should be closed.
- **Explicit abort.** `close()` without committing. The source is told
  to discard, and the object becomes `ABORTED` during release. No
  events.
- **Implicit abort.** Process death closes the fd, which aborts it.
  There are no orphaned transactions.
- **Timeout.** The lifetime timer fires. See below.

The object stays addressable after reaching a terminal state, until the
fd is closed. That is what makes `REG_IOC_TXN_STATUS` useful.

Transaction fds are pollable. Any terminal transition wakes poll
waiters with `POLLERR | POLLHUP`. A caller that needs a race-free
reason for the wakeup queries the status.

## Timeout

The lifetime timer starts when the fd is created — not at the first
operation — and runs for `TransactionTimeoutMs`, default 30 seconds.

When it fires, the object becomes `TIMED_OUT`, poll waiters are woken,
and further use of the fd returns `ETIMEDOUT`. If the transaction was
bound and no commit is already in flight, `RSI_ABORT_TRANSACTION` is
sent to the source. The fd is not removed from the caller's table;
`close()` still releases it normally.

The timeout is not a convenience. Sources serialise writers — loregd
does so through SQLite's WAL — so a stalled transaction blocks every
other write to that source. The timer is what bounds the starvation
window, and `MaxBoundTransactionsPerSource` (default 16) is what stops
colluding processes from extending it indefinitely by binding fresh
transactions at each timeout boundary. An operation that would bind
past that cap returns `EBUSY`.

The cap is tested before the source is contacted, but after the
transaction's mutation-log entry has been allocated; that entry is
freed on the way out.

## Constraints

- **No nesting.** Transactions are flat: no savepoints, no
  sub-transactions. The transaction fd accepts only `REG_IOC_COMMIT`
  and `REG_IOC_TXN_STATUS`; every other ioctl is `ENOTTY`.
- **One transaction per fd.** A process may hold many transaction fds
  at once, but each is exactly one transaction.
- **Reads are permitted.** A transaction is not write-only, which is
  what makes verify-then-write possible.

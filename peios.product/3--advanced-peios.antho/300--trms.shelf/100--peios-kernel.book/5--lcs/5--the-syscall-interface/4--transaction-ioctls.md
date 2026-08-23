---
title: Transaction Ioctls
description: The two ioctls acting on a transaction fd — commit and status — and why the key fd error table does not apply.
---

Two ioctls act on a transaction fd. Everything else on that fd is
`ENOTTY` — there are no savepoint or nesting operations to have.

The common key fd error table does not apply here.

## `REG_IOC_COMMIT`

Commits every operation in the transaction. §5.7.3 covers what happens
in each case; in summary:

| Errno | Condition |
|---|---|
| — | Success. The object becomes `COMMITTED`, poll waiters are woken, watch events are delivered, and further use of the fd returns `EINVAL`. |
| `EINVAL` | Already committed, or never bound to a source. |
| `EBUSY` | The source could not take the write lock. The transaction stays `ACTIVE_BOUND`; retry. |
| `EIO` | The source failed to commit. The transaction stays `ACTIVE_BOUND`. |
| `ETIMEDOUT` | The transaction timed out before the commit completed. |

`EBUSY` and `EIO` both leave the transaction usable: the mutation log
is retained, no events are emitted, and poll waiters are not woken as
though it had become terminal. The caller retries or closes the fd to
abort.

## `REG_IOC_TXN_STATUS`

Reports the transaction's state and a terminal errno into a
`reg_txn_status_args`. It reads nothing from the caller, consistent
with its `_IOR` direction, and can fail only with `EFAULT` on an
unwritable output pointer.

| State | `terminal_errno` |
|---|---|
| `REG_TXN_ACTIVE_UNBOUND` | 0 |
| `REG_TXN_ACTIVE_BOUND` | 0 |
| `REG_TXN_COMMITTED` | 0 |
| `REG_TXN_ABORTED` | `EINVAL` |
| `REG_TXN_TIMED_OUT` | `ETIMEDOUT` |
| `REG_TXN_SOURCE_DOWN` | `EIO` |

For the three failed terminal states, `terminal_errno` is the errno a
further operation on the fd would return. For `COMMITTED` it is not:
the transaction reports 0, but using the fd again returns `EINVAL`.

This ioctl is what makes a poll wakeup useful. A terminal transition
reports `POLLERR | POLLHUP`, which says only that *something*
terminal happened; the status call says what.

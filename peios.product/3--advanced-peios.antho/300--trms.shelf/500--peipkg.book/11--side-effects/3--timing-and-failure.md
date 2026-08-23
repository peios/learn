---
title: Timing and Failure
description: Side effects run at commit after every package is registered — what failure does, and what deliberately does not schedule one.
---

## Timing

Side effects run at transaction commit, after the database commit, after
every package in the transaction has completed extraction and
registration.

They are deduplicated across the transaction: several packages declaring
`ldconfig` produce one invocation. Distinct effects run in an
unspecified order, which is safe because the recognised set is chosen so
that order between them does not matter.

Running once, at the end, is what keeps the system consistent during a
multi-package install: the library cache is rebuilt after every
package's libraries are in place, not after each package individually
against a partial state.

## Failure

Side effects run after the durability boundary, so a failure cannot roll
the transaction back — the transaction is already committed.

A failure becomes a warning on the operation report and the transaction
stands. The operation exits successfully: the packages installed, and
only a cache lagged.

Because side effects are idempotent, a failed one is self-correcting.
Re-invoking it — explicitly, or as part of the next transaction that
declares it — reaches the correct state.

> [!NOTE]
> Rolling a committed transaction back because a cache rebuild exited
> non-zero would be disproportionate. The three recognised tools are
> stable with few failure modes outside system-level corruption, and
> every one of those failure modes is recoverable by running the tool
> again.

## What does not schedule

An operation that only removes files schedules nothing, so removing the
last package that owned a shared library or a kernel module leaves the
corresponding cache naming something that no longer exists (§7.6).

An upgrade does schedule effects implied by the files it removed, as
well as those the new version declares.

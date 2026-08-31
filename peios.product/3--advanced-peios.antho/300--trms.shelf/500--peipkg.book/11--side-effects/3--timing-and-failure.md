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

## Removals schedule too

A side effect runs when a transaction removes files whose absence
affects its target, as well as when it adds them. Removing the last
package that owned a kernel release's modules reindexes that release;
removing a package that shipped man pages reindexes the man database.

A removal declares nothing at the time — it has no incoming manifest —
so the declaration is read from the manifest stored for the package
being removed, and `depmod`'s affected release comes from that package's
ownership rows rather than from a payload.

An upgrade schedules effects implied by the files it removed as well as
those the new version declares.

---
title: What Is Not Recorded
description: The specific gaps in peipkg's audit trail — each a place where something happened and nothing was written — and how to read the trail knowing them.
---

The gaps in peipkg's audit trail are specific, and each one is a place
where something happened and nothing was written.

- An **install or upgrade event carries no source repository**, although
  one is known at the time.
- A **committed cross-root operation's success event carries no
  transaction identifier**, so it cannot be correlated with the rest of
  its transaction.
- **Automatic recovery** at the head of an ordinary operation emits
  nothing. Only recovery through `peipkg recover` produces
  `peipkg.recovery`.
- **`peipkg recover`'s failure paths** emit nothing. A recovery that
  fails leaves no record that it was attempted.
- **Declining at a prompt** emits nothing.
- **Enabling insecure transport** emits no authorisation record, and so
  does **installing unsigned content under an `optional` policy** — the
  two decisions most worth recording are the two that are not.
- **`peipkg-compose` emits nothing at all.** Image composition is
  entirely unaudited.

## Reading the trail with these in mind

Two consequences follow for anyone building on this stream.

**Absence is not evidence.** An operation with no event may have been
performed by a caller without the audit privilege, may have taken one of
the paths above, or may not have happened. The three are
indistinguishable from the stream.

**Transaction correlation is incomplete.** `txn_id` ties an operation's
events together, but the cross-root success case omits it, so a
reconstruction keyed on `txn_id` will silently drop those.

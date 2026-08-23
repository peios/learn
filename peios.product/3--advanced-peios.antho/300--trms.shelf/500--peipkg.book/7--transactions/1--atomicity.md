---
title: Atomicity
description: A transaction is the atomic unit of package work, with one durability boundary that everything commits across.
---

A transaction is the atomic unit of package work. Every install,
upgrade, uninstall, grant, and revoke executes within one, even when it
contains a single operation.

A transaction is atomic in the sense that either all of its operations
succeed and become visible, or none of them visibly take effect. That
holds under two kinds of failure:

- **Logical failure** — a step fails, an error is reported, or a
  cancellation is requested.
- **System failure** — power loss, kernel panic, hardware fault, at any
  point.

An **uncommitted** transaction is invisible to anything else on the
system: the database does not show its operations, staged files have not
replaced their targets, and no side effect has run. A transaction that
completes its commit step is **committed**, and its operations are
visible to everything afterwards.

## The single durability boundary

Atomicity rests on one fact: the package database is a transactional
store, and **the database's own commit is the transaction's durability
boundary**. No separate commit protocol is layered on top of it.

A crash before that commit leaves the journal's transaction pending, and
recovery rolls it back. A crash after it leaves the transaction
committed, and recovery has only cleanup to finish.

The transaction is never found partly committed, which is why recovery
never has to complete a half-finished commit.

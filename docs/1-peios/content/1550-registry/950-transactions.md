---
title: "Advanced: transactions"
type: concept
description: When several registry writes must take effect together or not at all, a transaction groups them into one atomic commit. It is a developer-facing tool — it is how a role installs without ever being half-applied. This page covers what transactions guarantee, their limits, and how they interact with the layered model.
related:
  - peios/registry/what-layers-are-for
  - peios/registry/layers
  - peios/registry/configuration-and-meaning
  - peios/registry/lcs-and-sources
  - peios/registry/overview
---

Most registry writes stand alone. But sometimes a set of changes only makes sense *together* — a role's keys and values are one coherent configuration, and a half-written version would be worse than none at all. A **transaction** makes several writes atomic: all of them commit, or none do. This is a developer-facing feature — you reach for it when *writing* to the registry, not when operating a running system — which is why it sits among the advanced topics.

## Transactions, in one sentence

**A transaction groups many registry writes into one all-or-nothing commit, so other readers only ever see the complete change, never a partial one.**

## All or nothing

Inside a transaction you perform a series of writes and then commit. At commit, they all take effect together. If you abort instead — or the process dies, or the transaction sits open too long and times out — none of them take effect. There is no partial application.

External readers see only committed state. Until you commit, your in-progress writes are invisible to everyone else; the instant you commit, the whole set appears at once. A service reading configuration never catches a transaction halfway. Within your own transaction you *do* see your own pending writes, so you can write a value and read it back before committing.

## The canonical use: installing a role

This is why [role installation](~peios/registry/what-layers-are-for) is clean. A role's entire configuration — its keys, its values, its layer — is written inside one transaction and committed as a unit. The role is never observed half-installed: either the whole role is there or none of it is. (Removing a role is the *other* mechanism — deleting its layer — covered with [layers](~peios/registry/what-layers-are-for).)

Any consistent multi-key update wants the same treatment: change several related settings as one atomic step, rather than letting readers see an inconsistent in-between.

## Limits worth knowing

- **One store at a time.** A transaction is scoped to a single hive's store; it cannot span hives backed by different [sources](~peios/registry/lcs-and-sources). Atomicity across separate stores is not offered.
- **No nesting.** Transactions are flat — there are no sub-transactions or savepoints.
- **Bounded lifetime.** An open transaction holds a write position, so it cannot be left open indefinitely; if it is not committed in time it is aborted automatically. This stops a stalled or abandoned writer from blocking everyone else's writes to that store.
- **Abandonment is safe.** Closing the handle without committing aborts cleanly, and a process dying does the same — there are no orphaned transactions left holding things up.

## Transactions and layers

A transaction provides *atomicity*; it is not a [layer](~peios/registry/layers) and it does not change which write wins. The two compose: a role install uses a transaction to apply its writes atomically *and* a layer to make them removable later. Keep them distinct — atomicity is "all together", layering is "which one wins, and how to revert".

Transactions are not conflict-detected at the value level. If two committed transactions wrote the same value, both succeed, and the usual rule settles it: the more recent write wins, exactly as in [layer resolution](~peios/registry/layers). A transaction guarantees its *own* writes land together; it does not lock anyone else out of the values it touched. (For the case where you must not clobber a concurrent change, a conditional write lets a single write proceed only if the value has not changed since you read it.)

## Where to start

For how a role uses a transaction and a layer together, read [What layers are for](~peios/registry/what-layers-are-for).

For the recency rule that settles competing writes, read [Layers](~peios/registry/layers).

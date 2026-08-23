---
title: Scope
description: What may go into one transaction, how operations are ordered, the one-operation-per-package rule, and cross-root transactions.
---

A transaction may contain any combination of installs, upgrades, and
uninstalls on different packages.

## Ordering

Operations are ordered so that at commit time no operation depends on a
package whose install has not been committed first. Forward operations
are topologically sorted dependencies-first; removals are sorted and
reversed, so a dependent is removed before what it depended on.

## One operation per package

A transaction cannot contain two operations affecting the same package.
This is structural rather than checked: the resolver's world is keyed by
(name, root) and emits at most one forward operation per key, deriving
removals as the complement.

An upgrade is how a version transition is expressed. A hard reinstall is
a removal and an install, in two separate transactions.

## Cross-root transactions

An operation touching several installation roots produces one
transaction per root, sharing a cross-root identifier. Locks are
acquired for every participating root, in resolved-path order, so that
two concurrent cross-root operations cannot deadlock against each other.

Each root's transaction is prepared and committed in sequence. That has
a consequence for verification (§5.1): one root's payload is in place
before the next root's packages have been fetched.

Recovery for a cross-root transaction is described in §7.8, and is the
one place where roll-forward exists.

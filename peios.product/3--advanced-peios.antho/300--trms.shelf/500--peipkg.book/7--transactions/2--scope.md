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

Every package of every participating root is fetched and verified before
any root is prepared. Verify-all-before-extract (§5.1) is an obligation
across the whole operation rather than within one root of it: a package
extracted into one root is as present on the filesystem as one extracted
into another, so preparing root by root would put one root's payload in
place before the next root's signatures had been looked at.

After that verification, every participant is prepared before the commit
loop begins. Preparation failure aborts and attempts to reverse prepared
changes; rollback errors can leave a pending journal. The commit loop then
attempts each prepared root's commit, continuing those attempts after a
failure and reporting a partial-commit error.

This ordering follows
[peipkg `8b588ae8`'s coordinated executor](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L230-L348).
It does not establish a globally atomic filesystem switch: preparation moves
files, and [post-commit maintenance](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L599-L655)
for one root can run before another root's commit is attempted.

[Cross-root recovery](~peios/peipkg/transactions/crash-recovery#cross-root-the-exception)
chooses rollback or roll-forward from participant state. See
[Named roots](~peios/package-management/named-roots#cascading-upgrade) for
operator checks and the pinned source/release scope.

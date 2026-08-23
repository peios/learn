---
title: Side-Effect Batching
description: Repeated side effects are deduplicated and invoked once per transaction, after every operation completes.
---

A transaction may contain several operations that each declare the same
side effect. They are deduplicated and invoked once per transaction,
after every file-level operation is complete and after the database
commit.

Distinct side effects are invoked in an unspecified order. The
recognised set is chosen so that order between them does not matter.

## Timing

Side effects are not invoked during extraction, and not once per
package. Installing ten packages that all ship shared libraries rebuilds
the library cache once, after every package's libraries are in place —
not ten times against ten partial states.

## What is not scheduled

An operation that only removes files schedules no side effects, because
side-effect declarations are read from the package being installed and a
removal has none in flight. The removed package's manifest is in the
database and could supply them.

The visible consequence: uninstalling the last package that owned a
shared library leaves the library cache naming a file that no longer
exists, and removing kernel modules leaves the module dependency cache
stale. Both are corrected by the next transaction that does declare the
relevant effect.

An upgrade is different: side effects implied by files the upgrade
removed are scheduled alongside those the new version declares.

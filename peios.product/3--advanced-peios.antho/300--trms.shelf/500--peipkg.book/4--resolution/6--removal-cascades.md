---
title: Removal Cascades
description: Removing a package others depend on — blocking relations, cascading, and the system-critical packages that refuse either.
---

Removing a package that other installed packages depend on would leave
the system inconsistent, so peipkg does one of two things, chosen per
transaction.

**Refuse** is the default. The removal is rejected and the dependents
that block it are named.

**Cascade** removes the dependents too. It is requested with
`--cascade`, and it is the operator taking responsibility for a larger
change than they typed.

Removals are ordered in reverse dependency order, so a dependent is
always removed before the package it depended on.

## Blocking relations

A removal is blocked by an installed package that depends on the one
being removed, and by an installed package whose `replaces` targets it.
Both are computed against the state the transaction will produce, so a
dependent that is itself being removed in the same transaction does not
block.

## System-critical packages

Some packages are needed for peipkg itself, or for the system, to work:
peipkg's own binary and its trust anchors, and the core system packages.

The intended guard is a refusal unless the operator supplies an
operation-specific override — an `--allow-critical` flag — which is a
foot-gun guard rather than a security boundary: under the access model
the operator already holds whatever authority the underlying deletions
require, so the guard exists to prevent an accidental removal disabling
the system, not to deny an authorised operator who means it.

peipkg has no notion of a system-critical set, no such flag, and no
guard. Uninstalling the package manager is an ordinary removal.

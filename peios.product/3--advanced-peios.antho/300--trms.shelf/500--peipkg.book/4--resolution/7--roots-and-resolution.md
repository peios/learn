---
title: Roots and Resolution
description: A dependency is satisfied within one root — the two resolution modes, top-level placement, and cascading across roots.
---

A dependency is satisfied within a specific installation root. By
default that is the same root as the depending package, so a package's
closure flows into the root the package occupies. A dependency's `root`
field overrides that, naming a different one.

## Two resolution modes

peipkg resolves in one of two modes.

**Cross-root** resolution honours a dependency's `root` field, placing
the dependency in the root it names and producing a plan whose
operations are grouped by root.

**Single-root** resolution treats every operation as belonging to one
root. A dependency carrying a `root` field is placed in the depending
package's root instead, and the field has no effect.

`install` resolves cross-root. Default `upgrade` also uses cross-root
resolution in [peipkg `8b588ae8`](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L188-L223);
`--no-recurse` confines upgrade resolution and execution to the current
root. The [cross-root dependency chapter](~peios/peipkg/installation-roots/cross-root-dependencies#which-verbs-route)
keeps that source-backed distinction separate from the earlier descriptions
of `downgrade`, `uninstall`, and `undo`, whose paths are not verified by
this upgrade correction.

## Top-level placement

Where an operator names a package directly with no explicit root, the
package's `default_root` decides where it lands. A dependency's
placement is never governed by the dependency's own `default_root`; only
by the depending package's root and the dependency's `root` field.

## Cascading across roots

Default upgrade resolves the current root and its reachable named roots
into one plan, with one approval. A named package is considered in each
reachable root where it is installed. If the plan changes multiple roots,
the [coordinated executor](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/install/execute.go#L230-L348)
verifies all packages, prepares the participants, then attempts commits
root by root. Preparation failure attempts rollback; a commit failure can
leave partially committed work needing recovery. These are not independent
continue-on-error upgrade transactions.

See [Named roots](~peios/package-management/named-roots#cascading-upgrade)
for operator checks and the pinned source/release scope, and
[transaction scope](~peios/peipkg/transactions/scope#cross-root-transactions)
for the execution boundaries.

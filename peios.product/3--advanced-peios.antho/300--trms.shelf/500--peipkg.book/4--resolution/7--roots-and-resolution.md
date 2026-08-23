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

`install` resolves cross-root. `upgrade`, `downgrade`, `uninstall`, and
`undo` resolve single-root.

The consequence is that a dependency declaring a root resolves into that
root when the depending package is first installed, and is evaluated
against — and if missing, installed into — the depending package's root
on any later upgrade or removal.

## Top-level placement

Where an operator names a package directly with no explicit root, the
package's `default_root` decides where it lands. A dependency's
placement is never governed by the dependency's own `default_root`; only
by the depending package's root and the dependency's `root` field.

## Cascading across roots

Upgrading a package that is installed in several roots produces one
transaction per root. Those transactions are applied in sequence and
continue past a failure: a root whose upgrade fails is reported, and the
remaining roots are still attempted.

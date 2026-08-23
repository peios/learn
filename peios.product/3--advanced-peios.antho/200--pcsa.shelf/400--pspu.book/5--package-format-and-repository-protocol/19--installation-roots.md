---
title: Installation Roots
description: A self-contained tree packages install into — the default root, named roots, and why dependency satisfaction is per-root.
---

An **installation root** is a self-contained filesystem tree into which
packages are installed. The default root is the system root; a system
MAY define additional **named roots** — an initramfs image built and
maintained alongside the main system is the motivating case.

How roots are registered, and how a name resolves to a filesystem
location, is consumer mechanics and is not part of the package format.

## Root references

A **root reference** is the string form by which a manifest names a
root. Within a manifest a root reference MUST be a **named reference**:
one or more segments separated by `.`, where each segment matches
`[a-z0-9][a-z0-9_-]*`. Nesting is expressed by further segments, so
`initramfs.subroot` names the root `subroot` registered within the root
`initramfs`.

A root reference in a manifest MUST NOT be an absolute or relative
filesystem path. A package names roots and never dictates a filesystem
location: placement is the installing system's prerogative.

A manifest whose root reference is not syntactically valid is invalid
and MUST cause the package to be rejected. Whether the named root
*exists* is a consumer-side resolution concern, not a format-validity
one.

## `default_root`

The manifest's `default_root` field (§5.18) governs **only** the
placement of a *top-level* install of the package — an operator request
naming this package directly, with no explicit root.

It has no effect when the package is pulled in as a dependency;
dependency placement is governed by the depending package and by the
dependency's own `root` field (§5.21). An explicit operator-supplied
root always overrides `default_root`.

## Satisfaction is per-root

The identity of a satisfier is the pair **(name, root)**. The same
package name installed in two different roots is two independent
satisfactions, possibly at different versions, and a dependency is
satisfied only by an installation in the named — or defaulted — root.
A `constraint` or architecture qualifier is evaluated against that
installation.

> [!NOTE]
> Cross-root dependencies let a root be composed through the dependency
> graph. An initramfs package may depend on ordinary packages — a shell,
> core utilities — and have them placed into the initramfs root, either
> implicitly by living in that root itself or explicitly through the
> dependency's `root` field. The depended-on package declares no root
> affinity of its own; where it lands is the depender's and the
> operator's choice. This generalises the fixed build-host/target split
> other systems draw to an open set of named roots.

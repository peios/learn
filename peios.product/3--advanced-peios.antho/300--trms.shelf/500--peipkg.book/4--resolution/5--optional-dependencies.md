---
title: Optional Dependencies
description: An optional dependency never enters a plan automatically, and is not carried into the resolver at all.
---

An optional dependency is never included in a plan automatically.

peipkg does not carry optional dependencies into the resolver at all:
they are not part of the candidate model, so there is no path by which
one could be installed without being asked for. An operator who wants
one names it as a goal.

A package whose optional dependencies are absent functions correctly
with reduced capability. A package that does not function without an
"optional" dependency has mis-categorised it — that is a required
dependency wearing the wrong label.

Optional dependencies still participate in claims. A claim path declared
on an optional-dependency entry is an *optional claim consumer* (§9.6):
the dependency need not be satisfied for the declaring package to
install, and the path is materialised only if and when some eligible
provider holds the role.

> [!NOTE]
> The pattern this supports: a service that would use a log sink if one
> existed, and ships without one. It declares the sink's runtime path as
> an optional claim, installs with no provider present, and the path
> simply does not exist. Installing a provider later materialises the
> path retroactively against the declaring package's declaration;
> removing the provider again withdraws it, with no effect on the
> declaring package.

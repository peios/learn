---
title: Relationships
description: What a package needs and offers, its dependencies, requirements and provides, with their constraints, and what satisfies each.
---

A manifest's `[dependencies]`, `[requires]`, and `[provides]` tables say what
the package needs and what it offers.

## Dependencies

A **dependency** is on another package, by name (§5.3), with a constraint
(§5.7):

```toml
[dependencies]
"se.curl.libcurl" = "= 8.22.0-1"
"dev.peios.base" = ""
```

A package that has the name, at a version the constraint holds for,
satisfies it. The empty constraint holds for any version.

## Requirements

A **requirement** is on a capability (§5.4), with a constraint:

```toml
[requires]
"libc.so.6" = ">= 2.34"
"sh" = ""
```

A package satisfies it if it provides the capability at a version the
constraint holds for, or provides it with no version, which holds for any
constraint; or if the capability is the package's own name and the
constraint holds for the package's version.

## Provides

A **provide** offers a capability, at a version or at none:

```toml
[provides]
"libcurl.so.4" = ""
"curl" = "8.22.0"
```

A provided version MAY leave out its revision (§5.7). A package provides its
own name at its own version without saying so.

## What ppk doesn't have

This version has no conflicts, replacements, or optional dependencies.
Packages that can't be composed together are refused when they are
(§5.24); one package taking over from another is a new version of a
package, or a new name that the old one's dependents are moved to.

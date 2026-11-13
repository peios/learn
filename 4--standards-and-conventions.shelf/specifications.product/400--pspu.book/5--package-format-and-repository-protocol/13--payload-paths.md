---
title: Payload Paths
description: A package's paths are relative to /usr, the constraints on them, the reserved path, and why nothing is canonicalized.
---

Every path a package holds is relative to `/usr`: a package's `bin/hello`
is `/usr/bin/hello`. A package installs nothing outside `/usr` but the
links it claims (§5.23).

## Constraints

A path MUST be relative, and MUST NOT contain an empty component, `.`,
`..` or a NUL byte. It MUST be valid UTF-8. It is compared byte for byte:
nothing is canonicalized, so two paths that differ in case or in Unicode
normalization are two paths.

## The reserved path

The top-level path `inventory`, that is `/usr/inventory`, is the closure's
inventory (§5.25). A package MUST NOT hold it, or anything beneath it,
whether as a file, a directory or a link, and MUST NOT claim it.

## An empty package

A package with no paths is valid. It installs nothing, and exists for what
it depends on and provides.

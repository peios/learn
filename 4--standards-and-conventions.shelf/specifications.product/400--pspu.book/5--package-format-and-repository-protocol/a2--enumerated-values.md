---
title: Enumerated Values
description: Every closed set of this chapter, architectures, pre-release tokens, constraint operators, entry kinds, license classes, standings and pointer-file lines.
---

## Architectures (§5.8)

`x86_64`, `aarch64`, `noarch`.

## Pre-release tokens (§5.6)

In rank order: `dev`; `alpha`, `a`; `beta`, `b`; `pre`; `rc`. A `~` begins a
pre-release too.

## Constraint operators (§5.7)

`=`, `>`, `>=`, `<`, `<=`, `!=`.

## Hash algorithms (§5.9)

`sha256`.

## Entry kinds (§5.16, §5.18)

`blob`, with `exec`, `descriptor` and `signature`; `symlink`; `dir`, with
`descriptor`.

## Manifest tables (§5.18)

`[claims]`, `[dependencies]`, `[provides]`, `[requires]`, `[files]`.

## Descriptive fields (§5.19)

`description`, `homepage`, `license`, `license_class`, `source_license`.

## License classes (§5.19)

`free`, `firmware`, `proprietary`, `unknown`.

## Standings of a version in a catalog (§5.31)

Current (nothing written), `yanked`, `deleted` and a reason.

## Pointer-file lines (§5.32)

`sequence`, `signed`, `catalog`, `index`, `channel`, with `ended`.

## Reserved closure names (§5.27)

`SYSTEM`, `INITRAMFS`.

## Profile keys (§5.28)

`arch`, `include`, `packages`, `symlinks`, `dirs`, `include_artifacts`.

## Repository configuration keys (§5.35)

`path`, `key`, `track`.

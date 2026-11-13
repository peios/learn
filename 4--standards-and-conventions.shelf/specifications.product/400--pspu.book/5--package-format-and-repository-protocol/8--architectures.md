---
title: Architectures
description: The architecture identifier, the defined set, the triplets derived from them, and how one resolution takes one architecture.
---

A package's architecture identifies the instruction-set architecture its
files are for. It is part of the package ID, separate from the name and the
version.

## Identifier format

An architecture identifier MUST consist of ASCII letters, digits, `.`, `_`,
`+`, `-` and `~`, and MUST start with a letter or a digit.

## Defined architectures

| Identifier | Meaning |
|---|---|
| `x86_64` | 64-bit x86 (AMD64, Intel 64) |
| `aarch64` | 64-bit ARM (ARMv8-A or later) |
| `noarch` | Content that doesn't depend on the architecture |

`x86_64` is the primary target. A new identifier SHOULD be the Linux
machine name, as `uname -m` reports it, where there is one.

## Triplets

Each architecture but `noarch` has a **triplet**,
`<identifier>-linux-peios`, used in the paths where architecture-specific
content is kept apart (§5.15): `x86_64-linux-peios`, `aarch64-linux-peios`.
`noarch` has none.

> [!NOTE]
> The `peios` suffix tells Peios binaries from other systems' binaries for
> the same architecture: Debian uses `gnu`, Alpine `musl`.

## One architecture per resolution

A resolution (§5.29) chooses packages of one architecture: the one its
requests name, or the consumer's own. A package of another architecture,
`noarch` included, is not a candidate in it.

> [!NOTE]
> This version doesn't let a resolution for `x86_64` choose a `noarch`
> package. Content that doesn't depend on the architecture is packed for
> each architecture instead. A future version can let `noarch` packages
> join any resolution without changing the format.

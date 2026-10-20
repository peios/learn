---
title: Architectures
description: The architecture identifier, the defined set, the triplets derived from them, and what noarch means for installability.
---

A package's architecture identifies the instruction-set architecture its
binaries were built for. It is a separate identifier from the name and
the version.

## Identifier format

An architecture identifier MUST consist of lowercase letters `a`–`z`,
digits `0`–`9`, and the underscore `_`. It MUST start with a lowercase
letter and MUST NOT exceed 16 characters.

## Defined architectures

| Identifier | Meaning |
|---|---|
| `x86_64` | 64-bit x86 (AMD64, Intel 64) |
| `aarch64` | 64-bit ARM (ARMv8-A or later) |
| `noarch` | architecture-independent |

An implementation MUST recognise all three. `x86_64` is the primary
target; every other architecture is secondary in this version of the
specification.

Additional identifiers MAY be defined in a future version. A new
identifier MUST satisfy the format above and SHOULD be the canonical
Linux machine name — the value `uname -m` reports — where one exists.

## Triplets

Each architecture identifier that is not `noarch` has a corresponding
**triplet**, used in the install paths where arch-specific content is
namespaced (§5.15):

```
<identifier>-linux-peios
```

| Identifier | Triplet |
|---|---|
| `x86_64` | `x86_64-linux-peios` |
| `aarch64` | `aarch64-linux-peios` |

`noarch` has no triplet form, and architecture-independent payload MUST
NOT be installed under an arch-namespaced path.

> [!NOTE]
> The `peios` suffix distinguishes Peios binaries from foreign-arch
> binaries originating elsewhere — Debian uses `gnu`, Alpine uses
> `musl`. It leaves room for a future multi-architecture system to host
> foreign-distribution binaries without filesystem-path collisions.

## Architecture-independent packages

The `noarch` identifier denotes a package whose payload contains no
architecture-dependent content: documentation, configuration templates,
scripts in interpreted languages, or metadata only.

A package MUST NOT declare `noarch` if its payload contains compiled
binaries, shared libraries, or any other content whose semantics depend
on the target architecture.

## Installability

Each Peios system has a single **primary architecture**, fixed at
install time.

- A package whose architecture equals the system's primary architecture
  MAY be installed.
- A package whose architecture is `noarch` MAY be installed on any
  system.
- A package whose architecture is neither MUST NOT be installed.

> [!NOTE]
> This version of the specification does not define multi-architecture
> systems — systems installing foreign-architecture packages alongside
> native ones. Running foreign-architecture binaries for emulation,
> cross-compilation, or legacy compatibility is addressed by mechanisms
> outside the package format. The triplet convention above applies
> regardless, so that a package conforming to this version stays
> forward-compatible with such an extension.

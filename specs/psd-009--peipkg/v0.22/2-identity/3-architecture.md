---
title: Architecture
---

A package's architecture identifies the target hardware
instruction-set architecture for which the package's binaries
were built. Architecture is a separate identifier from the
package name and the version string.

## Identifier format

An architecture identifier MUST consist of ASCII characters
from the following set:

- Lowercase letters `a` through `z`
- Digits `0` through `9`
- Underscore `_`

The identifier MUST start with a lowercase letter.

The identifier MUST NOT exceed 16 characters.

## Canonical architectures

The following architecture identifiers are defined by this
specification:

| Identifier | Meaning |
|---|---|
| `x86_64` | 64-bit x86 (AMD64, Intel 64) |
| `aarch64` | 64-bit ARM (ARMv8-A or later) |
| `noarch` | Architecture-independent |

Implementations MUST recognise these identifiers.

`x86_64` is the primary target architecture for Peios. All
other architectures are SECONDARY targets in this version of
the specification.

## Architecture triplets

Each architecture identifier has a corresponding *triplet*
form used in install paths where libraries and other
arch-specific resources are namespaced by architecture
(see §3.4 for payload paths).

The triplet form is constructed as:

```
<identifier>-linux-peios
```

| Identifier | Triplet |
|---|---|
| `x86_64` | `x86_64-linux-peios` |
| `aarch64` | `aarch64-linux-peios` |

The `noarch` identifier has no triplet form. Architecture-
independent payload MUST NOT be installed under
arch-namespaced paths.

> [!INFORMATIVE]
> The `peios` suffix in the triplet distinguishes Peios
> binaries from foreign-arch binaries that may originate from
> other distributions (Debian uses `gnu`, Alpine uses `musl`).
> This allows future multi-arch operation to coexist with
> foreign-distro binaries without filesystem-path collisions.

## Architecture-independent packages

The `noarch` identifier denotes packages whose payload contains
no architecture-dependent binaries. Typical contents include
documentation, configuration templates, scripts written in
interpreted languages, and packages whose payload is
metadata-only.

A `noarch` package MAY be installed on any system regardless
of that system's hardware architecture.

A package MUST NOT use the `noarch` identifier if its payload
contains compiled binaries, shared libraries, or any other
content whose semantics depend on the target architecture.

## Resolution

Each Peios system has a single primary architecture, identified
at install time and recorded in the system's package database
state.

A package whose architecture matches the system's primary
architecture MAY be installed.

A package whose architecture is `noarch` MAY be installed on
any system.

A package whose architecture differs from the system's primary
architecture and is not `noarch` MUST NOT be installed.

> [!INFORMATIVE]
> This specification does not define multi-architecture systems
> (systems that install foreign-architecture packages
> alongside native ones). Use cases that require running
> foreign-architecture binaries -- such as emulation,
> cross-compilation, or container-based legacy compatibility --
> are addressed by mechanisms outside the package format.

## Future architectures

Additional architecture identifiers MAY be defined in future
versions of this specification. New identifiers MUST follow
the format constraints above (§2.3.1) and SHOULD use the
canonical Linux machine name (the value reported by
`uname -m`) when one exists.

## Filename position

The architecture identifier appears in the package filename
as the third field, separated from the version by a single
underscore (§2.1.4):

```
<name>_<version>_<architecture>.peipkg
```

The architecture identifier appears in the package URL as
part of the package filename (§6.4):

```
/p/<name>/<version>/<name>_<version>_<architecture>.peipkg
```

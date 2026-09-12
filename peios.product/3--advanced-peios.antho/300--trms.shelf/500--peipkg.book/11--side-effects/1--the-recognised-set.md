---
title: The Recognised Set
description: A package cannot ship install-time code; it declares one of three standard maintenance operations, and peipkg runs it.
---

A package cannot ship code that runs at install time. It can declare
that one of two standard maintenance operations is required, and
peipkg invokes it.

| Identifier | Rebuilds |
|---|---|
| `depmod` | The kernel module dependency cache — `modules.dep` and its companions under `/usr/lib/modules/<release>/` |
| `man-db` | The man page index, `/var/cache/man/index.db` or its equivalent, which `apropos` and `whatis` read |

The set is closed. A manifest declaring anything else — `ldconfig`
included: Peios has one shared-library directory and no loader cache
(§5.24) — is rejected, and a duplicate within the array is rejected.

## When each is required

A package containing kernel modules declares `depmod`; one containing
none does not. A package containing man pages is expected to declare
`man-db` — a recommendation rather than a requirement, because man page
lookup degrades to a filesystem scan without it.

peipkg validates the declared values against the enumeration. The
consumer does not validate them against the payload; the producer's
packer does, refusing a payload whose kernel modules and `depmod`
declaration disagree in either direction. A package built elsewhere
that declares `depmod` with no modules behind it runs nothing at install
time and is reported as a warning (§11.2).

## What side effects are not

- Not a general install-script mechanism. The closed enumeration is
  precisely what prevents arbitrary code execution at install time.
- Not a way to register a service. Service integration belongs to the
  higher-level artifacts that compose packages.
- Not a way to seed registry state.
- Not a way to apply security descriptors, which belong to file
  creation.

A package whose required behaviour cannot be expressed through the
manifest is incomplete and cannot be installed through the package
format alone. That behaviour is supplied by the artifact that composes
the package.

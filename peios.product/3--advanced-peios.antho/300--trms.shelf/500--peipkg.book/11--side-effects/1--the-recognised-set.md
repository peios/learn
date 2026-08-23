---
title: The Recognised Set
description: A package cannot ship install-time code; it declares one of three standard maintenance operations, and peipkg runs it.
---

A package cannot ship code that runs at install time. It can declare
that one of three standard maintenance operations is required, and
peipkg invokes it.

| Identifier | Rebuilds |
|---|---|
| `ldconfig` | The shared library cache, `/etc/ld.so.cache`, and shared library symlinks |
| `depmod` | The kernel module dependency cache — `modules.dep` and its companions under `/usr/lib/modules/<release>/` |
| `man-db` | The man page index, `/var/cache/man/index.db` or its equivalent, which `apropos` and `whatis` read |

The set is closed. A manifest declaring anything else is rejected, and a
duplicate within the array is rejected.

## When each is required

A package containing shared libraries declares `ldconfig`; one
containing none does not. A package containing kernel modules declares
`depmod`; one containing none does not. A package containing man pages
is expected to declare `man-db` — a recommendation rather than a
requirement, because man page lookup degrades to a filesystem scan
without it.

peipkg validates the declared values against the enumeration. It does
not validate them against the payload: a package shipping shared
libraries with no `ldconfig` declaration packs, installs, and leaves the
library cache stale, and a package declaring `ldconfig` while shipping
no libraries invokes it for nothing.

The producer is where that check belongs — the payload map it would
examine is already walked to derive shared-library capabilities — and
neither the producer nor the consumer performs it.

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

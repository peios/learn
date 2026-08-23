---
title: Licensing and source availability
type: concept
description: The licences Peios ships under, how every package declares and carries its licence, and how to obtain the corresponding source for any published binary.
related:
  - project/policies/security-policy
---

Peios is open source. This page states the licensing terms and the mechanisms that carry them through the packaging pipeline.

## First-party code

First-party Peios components are licensed under the **MIT licence**, copyright **The Peios Authors**. The exception is the PKM kernel tree: it is a derivative work of the Linux kernel and is therefore licensed **GPL-2.0-only** (with the Linux syscall exception), like the kernel itself.

## Package licence metadata

Every Peios package declares its licence as an [SPDX expression](https://spdx.org/licenses/) in its manifest — `GPL-3.0-or-later WITH GCC-exception-3.1`, `BSD-3-Clause`, and so on.

The package format itself treats the field as optional, but **pekit requires it** for any `peipkg`-format package, so every package Peios publishes carries one. The metadata is complete by construction rather than by convention.

The licence texts themselves install with the software, under `/usr/share/licenses/<package>/`. Composed images additionally carry an aggregate inventory at `/usr/share/licenses.json`, listing every installed package with its version, licence expression, and source reference — an image can always answer what it contains and under what terms.

## Corresponding source

For every package built from an external source, Peios publishes a companion **source package** (`<name>-source`) through the same channel as the binary. It installs under `/usr/src/dist/<name>-<version>/` and contains:

- `upstream/` — the pristine source input the build consumed, byte-for-byte; its hash matches the build recipe's committed lockfile, so you can verify it independently.
- `patches/` — the patch series Peios applied, when there is one.
- `recipe/` — the build recipe itself: the scripts that control compilation and installation.

Each binary package names its source package in its manifest, in the `source_package` field, and the aggregate inventory carries the same mapping. This is how Peios meets the source-availability obligations of copyleft licences such as the GPL: the corresponding source of every published binary is available from the place you got the binary, for as long as the binary is distributed.

Details of how source packages are produced are in the pekit documentation: [sources and the lockfile](~pekit/recipes/sources).

## Where to go next

- [Security policy](~project/policies/security-policy) — how to report a vulnerability.

---
title: The Architecture Triplet
description: What an architecture-specific package must install under /usr/lib/<triplet>/, the exemptions, and where architecture-independent data goes.
---

A package whose architecture is not `noarch` MUST install all of the
following under `/usr/lib/<triplet>/`, where `<triplet>` is the
architecture triplet of §5.8:

- shared libraries (`.so`, `.so.*`)
- static libraries (`.a`)
- loadable modules — plugin shared objects, and kernel modules outside
  `/usr/lib/modules/`
- architecture-*dependent* helper binaries not on the user's search path
- any other arch-dependent file that is not a user-facing binary

Architecture-*independent* helper executables — a shell script run by
another program, say — go under `/usr/libexec/` instead, which carries
no triplet rule because the rule is scoped to `/usr/lib/`.

A package whose architecture is `noarch` MUST NOT install any file under
`/usr/lib/<triplet>/`. A `noarch` package containing any of the
categories above is invalid.

## Exemptions

Three arch-dependent payload categories are exempt from the triplet
path, because each is addressed by something other than the host
triplet:

| Category | Path | Addressed by |
|---|---|---|
| Kernel content | `/usr/lib/modules/<release>/` | kernel release |
| Device firmware | `/usr/lib/firmware/` | device |
| Separated debug information | `/usr/lib/debug/` | the install path of the file it describes |

A `noarch` package MUST NOT install under `/usr/lib/modules/` or under
`/usr/lib/debug/`: kernel content and debug information are both
arch-dependent. `/usr/lib/firmware/` carries no such restriction,
firmware being opaque data rather than host-architecture content.

Debug files mirror the full install path of what they describe. The
debug information for `/usr/bin/foo` is
`/usr/lib/debug/usr/bin/foo.debug`; for `/usr/lib/<triplet>/libfoo.so.1`
it is `/usr/lib/debug/usr/lib/<triplet>/libfoo.so.1.debug`. Debug files
MAY additionally be indexed by build ID under
`/usr/lib/debug/.build-id/`.

The freedesktop `os-release` file is a fourth exemption of a different
kind: it installs at exactly `/usr/lib/os-release`, a fixed external
contract path the ecosystem hard-codes. Unlike debug information it is
arch-*independent*, so a `noarch` package — the OS-identity package —
MAY ship it. It is conventionally paired with a `/usr/etc/os-release`
symlink, which the `/etc` merge projects to `/etc/os-release`.

## Source

The debugger *source* files that debug information references install
under `/usr/src/debug/`, not under `/usr/lib/`. Source is
architecture-independent, so `/usr/src/debug/` carries neither a triplet
rule nor the `noarch` restriction: it is a plain permitted destination
that both arch-specific and `noarch` packages MAY use. The same applies
to `/usr/src/dist/`, the home of corresponding-source packages.

> [!NOTE]
> A corresponding-source package conventionally lays out
> `/usr/src/dist/<name>-<version>/` with `upstream/` — the pristine
> source artifact, byte-identical to the producer's pinned input —
> `patches/` for the applied patch series, and `recipe/` for the
> build-controlling recipe files including the source lock that makes
> the shipped upstream artifact verifiable. This is a producer
> convention, not a format rule.

## Architecture-independent data

`/usr/share/` holds architecture-independent files shared across every
architecture of a system: documentation, man pages, locales,
configuration templates, and static data such as icons, images, and
fonts.

Both `noarch` and arch-specific packages MAY install under
`/usr/share/`. A file installed there by an arch-specific package MUST
be byte-identical across every architecture build of the same upstream
version.

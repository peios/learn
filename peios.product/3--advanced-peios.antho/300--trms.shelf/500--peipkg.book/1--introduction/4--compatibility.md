---
title: Compatibility
description: Which format and protocol version peipkg implements, the architectures it supports, and how it interoperates.
---

## Format and protocol version

peipkg implements `schema_version` 1 of every document in PSPU §5: the
manifest, the files manifest, the signature envelope, the repository
descriptor, and both indexes. It rejects any other value, and rejects
any value outside a closed enumeration — a side-effect identifier, a
hash or signature algorithm, a key status, an index kind, a signature
policy — rather than ignoring it.

Unknown *fields* are ignored everywhere except the signature envelope,
which is parsed strictly.

## Architectures

`x86_64` is the primary target and the one the system is built and
tested for. `aarch64` is recognised and is a secondary target.

Architecture identifiers are validated for *format* wherever they
appear, but membership of the canonical set is not itself checked: a
package declaring an architecture peipkg has never heard of parses
cleanly and is simply not installable, because it matches neither the
system's primary architecture nor `noarch`. This is the behaviour a
future architecture addition needs, and it means an unrecognised
architecture produces a resolution failure rather than a parse failure.

The system's primary architecture is recorded in the package database at
first use. When no value is recorded, peipkg derives one from the
architecture it was itself built for.

## Multi-architecture

Only one architecture's packages may be installed on a system at a time,
alongside `noarch` packages. The architecture triplet convention (PSPU
§5.15) applies regardless, so that today's packages stay compatible with
a future extension that lifts the restriction.

## The producer toolchain

pekit is the producer. It builds through the same packing library peipkg
reads with, so a package that packs has already been decoded by the
consumer's own validators. Recipes are versioned by convention rather
than by a schema field: a tool tolerates a top-level section it does not
own and rejects an unknown key within a section it does.

## Interoperability

A package is a Zstandard-compressed pax tarball and can be inspected
with ordinary tools. Extracting one on a non-Peios host yields
world-writable files, because every entry is mode `0777` by design
(PSPU §5.16); applying sensible host-native permissions afterwards is
the extracting tool's job.

A repository is static files over HTTP. Anything that can serve a
directory tree can host one, and anything that can fetch a URL and
verify an Ed25519 signature can consume one.

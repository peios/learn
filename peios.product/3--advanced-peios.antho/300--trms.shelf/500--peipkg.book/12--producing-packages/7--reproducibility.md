---
title: Reproducibility
description: The format's determinism rules are necessary but not sufficient — what the build has to control, and how to verify a package reproduces.
---

A package is reproducible when the same inputs produce byte-identical
output. The format's determinism rules (PSPU §5.11) are necessary but
not sufficient: they constrain what the archive looks like, not how the
producer arrived at its contents.

## What the format fixes

Entry ordering, modification times tied to the recorded build timestamp,
uniform ownership and mode, no extended attributes, canonical extended
header records, and a fixed header format. Given the same uncompressed
tar stream and the same key, the signature is deterministic too.

## What it does not fix

**Compression.** The level, the implementation, its version, and its
frame parameters all change the resulting bytes and none is constrained.
pekit pins its own choice, so pekit reproduces pekit; two producers
seeking byte-identical output have to agree on compression out of band.

**Manifest serialisation.** The manifest's bytes are inside the archive
that gets hashed and signed, so two semantically identical manifests
with different whitespace produce different packages. pekit's
serialisation is compact, unescaped, with a single trailing newline,
with fields in schema order and a fixed rule about which optional fields
are always emitted. That is pinned in the producer rather than in the
format.

## What the build has to control

Everything the build process can observe: timestamps, file ordering,
locale, environment, ambient filesystem state, and build paths.

The established techniques apply. `SOURCE_DATE_EPOCH` gives every build
tool one timestamp to stamp its outputs with. A sealed environment — a
container or a virtual machine — pins the full build dependency closure,
which is itself a build input that determines the output. `LC_ALL=C` and
`TZ=UTC` suppress locale-dependent ordering and time formatting. And
build-path normalisation keeps absolute paths out of debug information
and out of anything else a compiler embeds.

## Verifying it

The manifest records the build's farm identifier, its source reference,
optionally the recipe tree's version-control identity and the producing
tool's revision, and the timestamp. A third party with the same inputs
can re-run the build and compare the output bytes.

The format supplies the inputs for that verification and does not
mandate it.

## Before publishing

Worth checking before a package is published: that its hash matches what
was recorded, that its signature verifies against the publishing key,
that it installs cleanly in a fresh environment, that its dependency
declarations reference packages that exist and constraints that are
satisfiable, and that re-running the build from the same inputs produces
identical bytes.

The cost of catching an error before publication is low; the cost of a
published incorrect package is re-publication and a user-facing
rollback.

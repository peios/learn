---
title: The Container
description: A package is one Zstandard-compressed tar archive — the extension, tar format, compression settings, and what makes it streamable.
---

A package is a single file: a tar archive compressed with Zstandard.

## Extension

A package file's extension MUST be `.peipkg`. There is no intermediate
`.tar` form; a producer emits the compressed form directly, and the
compressed file is the whole artifact.

## Tar format

The tar archive MUST conform to the POSIX pax interchange format
(IEEE Std 1003.1-2017, Chapter 14).

> [!NOTE]
> pax supports arbitrary path lengths through extended headers. The
> older ustar format limits paths to 100 characters, or 255 with a
> prefix, which is not enough for some real packages. GNU tar,
> libarchive, and BSD tar all read and write pax by default.

## Compression

The archive MUST be compressed with Zstandard (RFC 8478).

The compression level is at the producer's discretion. zstd is
deterministic at every level, so a producer MAY choose any level to
trade build time against on-wire size. Levels 19 and above, including
`--ultra`, increase build time substantially for a smaller result; level
3 is a common default.

## Reproducibility

A package MUST be reproducible: given identical source inputs, an
identical build environment, identical metadata — including the build
timestamp recorded in the manifest — and identical compression
parameters, two independent producers MUST produce byte-identical
package files.

The determinism rules of §5.11 are what make this achievable at the
format level. They are necessary rather than sufficient: they constrain
what the archive looks like, not how the producer arrived at its
contents.

Byte-identity is a property of the **uncompressed** tar stream and of
the compression applied to it. This specification fixes the former
completely and the latter not at all: the compression level, the
Zstandard implementation, its version, and its frame parameters all
affect the resulting bytes and are none of them constrained here. Two
producers seeking byte-identical output MUST therefore agree on their
compression parameters out of band. What the format guarantees
unconditionally is that the *signed* bytes — the uncompressed tar
prefix of §5.28 — are identical, so a signature survives recompression
at any level.

## Streaming

A consumer MAY process the archive as a stream. The internal layout
(§5.12) places metadata before payload precisely so that a consumer can
read a package's identity and reject a mismatched package without
buffering the payload.

## No outer wrapping

The compressed archive contains tar entries and nothing else: no
enclosing directory, no concatenated archives, no container metadata
outside the tar entries themselves.

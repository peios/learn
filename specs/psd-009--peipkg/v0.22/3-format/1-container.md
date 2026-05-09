---
title: Container
---

A package is a single file containing the package's payload
and metadata. The on-wire form of a package is a Zstandard-
compressed tar archive.

## File extension

The package file extension MUST be `.peipkg`. The full file is
a tar archive compressed with Zstandard.

## Tar format

The tar archive MUST conform to the POSIX pax interchange
format (IEEE Std 1003.1-2017, Chapter 14).

> [!INFORMATIVE]
> The pax format supports arbitrary path lengths via PAX
> extended headers. The older POSIX ustar format limits paths
> to 100 characters (255 with prefix), which is insufficient
> for some real-world packages. Most modern tar
> implementations (GNU tar, libarchive, BSD tar) read and
> write pax format by default.

## Compression

The tar archive MUST be compressed using the Zstandard format
(RFC 8478).

The compression level is at the producer's discretion.
zstd is deterministic at all levels per RFC 8478;
producers MAY choose any level based on their build-time
versus decompression-time tradeoff. Higher levels (19 and
above, including `--ultra`) increase build time
substantially in exchange for smaller on-wire size; level
3 is a common default.

The compressed result is a single file with the `.peipkg`
extension. There is no intermediate `.tar` form on disk; the
producer's tooling produces the compressed form directly.

## Determinism

A package MUST be reproducible: given identical source
inputs, identical build environment, and identical metadata
(including the build timestamp recorded in the manifest),
two independent producers MUST produce byte-identical
package files.

To achieve this, the tar archive MUST follow these rules:

1. Tar entries MUST be ordered lexicographically by path.
   Comparison is byte-for-byte over the UTF-8 path string.
2. Every tar entry's modification time MUST equal the value
   of `build.timestamp` in the manifest (§3.3).
3. Every tar entry's owner numeric ID and group numeric ID
   MUST be 0 (root).
4. Every tar entry's owner name and group name MUST be the
   string `root`.
5. Tar entries MUST NOT carry extended attributes (xattrs).
   File security descriptors (PSD-004 §3.12) are applied at
   file-creation time via the kernel's file-creation
   interface (PSD-004 §11.2), supplied either by
   inheritance from the parent directory or from a
   manifest-declared override. See §3.4 for the SD
   application procedure. Other install-time attributes
   are applied via side-effect declarations (§4.3) or by
   higher-level integration mechanisms outside this
   specification.
6. Tar entry permission bits MUST be `0777` for every entry,
   with the setuid and setgid bits cleared (§3.4.6).
7. PAX extended header records, when present, MUST be in a
   fixed canonical order: `path` first, then `linkpath` if
   present, then any other records sorted by record name
   lexicographically.
8. Tar header magic MUST be `ustar\0` and version MUST be
   `00`.
9. Tar header `devmajor` and `devminor` fields MUST be 0
   for all entry types defined by this specification (none
   of which are device entries).
10. Tar header padding bytes MUST be NUL (`0x00`).
11. PAX global header records (typeflag `g`) MUST NOT
    appear in the archive.
12. PAX extended header records (typeflag `x`) MUST appear
    only when an entry's `path` exceeds the ustar 100-byte
    limit (in which case a `path` record is emitted) or its
    `linkname` exceeds the ustar 100-byte limit (in which
    case a `linkpath` record is emitted). Records with any
    other key MUST NOT be emitted.

## Streaming

A consumer MAY process the archive as a stream. The internal
layout (§3.2) is designed so that metadata appears before
payload, allowing a consumer to read the manifest and decide
whether to continue without buffering the entire payload.

## Top-level structure

The compressed tar archive contains entries laid out
according to the internal layout in §3.2. There is no
additional outer wrapping (no enclosing directory, no
multi-archive concatenation, no container metadata outside
the tar entries themselves).

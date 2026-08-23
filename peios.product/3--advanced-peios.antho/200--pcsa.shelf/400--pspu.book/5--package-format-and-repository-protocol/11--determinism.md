---
title: Determinism
description: The rules a tar archive must obey to be byte-reproducible, every one of which a consumer rejects a package for violating.
---

To make a package byte-reproducible (§5.10), the tar archive MUST obey
every rule below. A consumer MUST reject a package that violates any of
them.

1. Tar entries MUST be ordered lexicographically by **the entry name as
   written into the tar header**, compared byte-for-byte over its UTF-8
   bytes. A directory's entry name carries a trailing `/`, and that
   slash participates in the comparison.
2. Every entry's modification time MUST equal the value of
   `build.timestamp` in the manifest (§5.18), which MUST NOT carry
   sub-second precision.
3. Every entry's owner numeric ID and group numeric ID MUST be 0.
4. Every entry's owner name and group name MUST be the string `root`.
5. Entries MUST NOT carry extended attributes. Security descriptors are
   applied at file-creation time (§5.20), never through tar attributes;
   other install-time attributes are applied through side-effect
   declarations (§5.24) or by higher-level mechanisms outside this
   specification.
6. Entry permission bits MUST be `0777` for every entry, with the setuid
   and setgid bits cleared (§5.16).
7. PAX extended header records, when present, MUST appear in a fixed
   canonical order: `path` first, then `linkpath` if present, then any
   other record sorted by record name lexicographically.
8. The tar header magic MUST be `ustar\0` and the version MUST be `00`.
9. The `devmajor` and `devminor` header fields MUST be 0 for every entry
   type this specification permits — none of which is a device entry.
10. Header padding bytes MUST be NUL (`0x00`).
11. PAX global header records (typeflag `g`) MUST NOT appear.
12. PAX extended header records (typeflag `x`) MUST appear only when an
    entry's `path` exceeds the ustar 100-byte limit, in which case a
    `path` record is emitted, or its `linkname` exceeds that limit, in
    which case a `linkpath` record is emitted. A record with any other
    key MUST NOT be emitted.
13. A path exceeding the ustar 100-byte limit MUST be carried by a
    `path` record. The ustar `prefix` field MUST NOT be used to split
    such a path across `prefix` and `name`.
14. An extended header entry's own name MUST be the containing
    directory's path, then `PaxHeaders.0/`, then the base name of the
    entry it describes. For an entry at the archive root the directory
    part is absent.

Rules 13 and 14 exist because a tar library given a long path may
legitimately choose either encoding, and either choice produces a
different byte stream from the same input. Determinism requires the
choice be made here rather than by whichever library a producer reached
for.

> [!NOTE]
> Rule 2's sub-second prohibition is not fussiness. A timestamp carrying
> a fractional part forces an `mtime` extended header onto every entry,
> violating rule 12 across the whole archive and changing the block
> count of the signature entry's own header — which is exactly the
> quantity a verifier uses to find the end of the signed range (§5.28).
> The symptom is a signature that does not verify, reported against the
> key rather than against the timestamp.

> [!NOTE]
> Rules 3, 4, and 6 together make a payload identity-free and
> permission-free: bytes in transit, carrying no claim about who may
> read them. What access control an installed file gets is decided at
> install time (§5.20), not declared by the package. §5.16 states the
> consequence for anyone extracting a package with a generic tar tool.

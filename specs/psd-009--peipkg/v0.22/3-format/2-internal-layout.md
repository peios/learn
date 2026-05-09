---
title: Internal Layout
---

The contents of a package's tar archive are divided into
metadata entries (under a reserved prefix) and payload
entries (the files that will be installed on the target
system).

## Reserved metadata prefix

All metadata entries MUST appear under the path prefix
`.peipkg/` at the archive root. This prefix is RESERVED:
payload entries MUST NOT use any path beginning with
`.peipkg/`.

> [!INFORMATIVE]
> The `.peipkg/` prefix is conventional for package metadata
> and is unlikely to collide with real upstream content. The
> leading dot keeps it sorted before payload entries on most
> file managers.

## Required metadata entries

Every package MUST contain the following entries:

| Entry path | Purpose | Section |
|---|---|---|
| `.peipkg/manifest.json` | Authoritative package metadata | §3.3 |
| `.peipkg/files.json` | Per-file integrity manifest | §3.5 |
| `.peipkg/signature` | Inline package signature | §5.1 |

## Entry ordering

Tar entries MUST appear in the archive in the following
order:

1. `.peipkg/manifest.json`
2. `.peipkg/files.json`
3. All payload entries, sorted lexicographically by path
   (per §3.1.4)
4. `.peipkg/signature`

The manifest appears first so that streaming consumers can
read the package's identity and reject mismatched packages
(wrong name, wrong version, wrong architecture) before
reading the payload.

The signature appears last and signs the archive content
preceding it (§5.1 specifies what is signed and how).

## Optional metadata entries

A package MAY include additional entries under `.peipkg/`
for forward-compatible extensions. The set of entries
recognised by this specification is fixed (the three above);
unrecognised entries under `.peipkg/` MUST be ignored on
parse but MUST NOT prevent installation.

> [!INFORMATIVE]
> Future versions of this specification may introduce
> additional metadata entries (build attestations,
> reproducibility manifests, software bill-of-materials).
> Producers compatible with a future version MAY emit such
> entries in v0.22 packages; consumers conformant to v0.22
> ignore them.

When present, optional metadata entries MUST appear between
`.peipkg/files.json` and the first payload entry, sorted
lexicographically by path.

## Payload entries

Payload entries are tar entries with paths that do not begin
with `.peipkg/`. These are the files, directories, and
symlinks that the package installs on the target system.

## Permitted entry types

Tar payload entries MUST be of one of the following types:

- Regular file (typeflag `0` or `\0`)
- Directory (typeflag `5`)
- Symbolic link (typeflag `2`)

Tar entries of any other type MUST cause the package to
be rejected. This explicitly excludes:

- Hardlinks (typeflag `1`)
- Character devices (typeflag `3`)
- Block devices (typeflag `4`)
- FIFOs (typeflag `6`)
- Contiguous files (typeflag `7`)
- Vendor-specific types

> [!INFORMATIVE]
> Hardlinks are excluded because they share an inode with
> their target and would let a package install a payload
> entry that aliases an existing system file (granting
> shared access to that file). KACS hardlink-creation
> permissions (PSD-004 §14-B) provide some defense, but
> the format-level exclusion is simpler and avoids the
> entire class of attack. Device, FIFO, and contiguous
> entries have no use case in package payloads.

## Payload path constraints

Payload paths MUST be relative (MUST NOT begin with `/`).

Payload paths MUST NOT contain any segment equal to `.` or
`..` or any encoding thereof.

Payload paths MUST be valid UTF-8 (RFC 3629).

Payload paths MUST NOT contain NUL bytes (`0x00`) or any
ASCII control character (`0x01`-`0x1F`, `0x7F`).

Payload paths MUST NOT contain backslash (`\`) characters.

Payload paths MUST be in Unicode Normalization Form C (NFC)
per Unicode 16.0.

Each path component MUST be at most 255 bytes long when
encoded as UTF-8.

A complete payload path MUST be at most 4096 bytes long
when encoded as UTF-8.

A payload path MUST NOT begin with the prefix `.peipkg/`,
or with `.peipkg` followed by end-of-path (i.e., no payload
entry may be literally named `.peipkg`).

A consumer MUST validate every payload path against these
constraints before any further processing of the entry. A
package containing a non-conforming payload path MUST be
rejected.

The on-disk install location is the payload path resolved
against the filesystem root. Path resolution MUST NOT
canonicalise away `..` or `.` segments by interpretation;
such segments are forbidden in the input (above) and any
appearance is a format error, not a path-canonicalisation
question.

> [!INFORMATIVE]
> Example: a tar entry at path `usr/bin/nginx` installs to
> `/usr/bin/nginx` on the target system. A tar entry at path
> `usr/lib/x86_64-linux-peios/libssl.so.3` installs to
> `/usr/lib/x86_64-linux-peios/libssl.so.3`.

## Empty package payloads

A package MAY have zero payload entries. A package with no
payload contains only metadata; its install operation is
limited to recording the package in the system database and
running any side-effect declarations (§4.3).

> [!INFORMATIVE]
> Empty-payload packages are useful as virtual aggregators:
> a package that provides no binaries itself but declares
> dependencies on a curated set of other packages.

## Resource limits

To bound consumer-side resource usage during package
parsing, the format establishes minimum-conformance
limits. A consumer MUST process packages whose
characteristics fall within these limits and MUST reject
packages that exceed them.

| Limit | Maximum value |
|---|---|
| Number of payload entries | 100,000 |
| Manifest JSON size (`.peipkg/manifest.json`) | 16 MiB |
| Files manifest JSON size (`.peipkg/files.json`) | 64 MiB |
| Signature envelope JSON size (`.peipkg/signature`) | 64 KiB |
| Single payload path component (UTF-8 bytes) | 255 |
| Complete payload path (UTF-8 bytes) | 4096 |
| Path nesting depth (number of components) | 256 |
| `dependencies` array length | 10,000 |
| `optional_dependencies` array length | 10,000 |
| `conflicts` array length | 10,000 |
| `provides` array length | 10,000 |
| `replaces` array length | 1,000 |
| `sd_overrides` array length | 100,000 |
| Single SD override `sd` field decoded length | 64 KiB |

A consumer MAY raise these limits via operator
configuration but MUST NOT raise them silently;
operator-tuned values SHOULD be logged and surfaced in
diagnostic output.

A producer SHOULD stay well below these limits in
practice. The limits exist to bound consumer resource
usage when processing maliciously-crafted packages, not
to define the typical scale of a well-formed package.

> [!INFORMATIVE]
> The decompression-bound rules in §3.5.4 are independent
> of these per-entity limits. A package can fall within
> all the limits in this table and still trigger a
> decompression-bound rejection if its uncompressed size
> exceeds `size_installed` plus the 1% allowance.

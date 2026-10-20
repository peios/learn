---
title: Verifying a Package
description: The ordered steps a consumer performs before installing anything, why nothing is observable before step three, and how a transaction commits.
---

A consumer MUST perform the following steps, in this order, before
installing anything from a package:

1. Compute the SHA-256 of the downloaded `.peipkg` file.
2. Compare it against the hash recorded in the repository index (§5.33).
   If they differ, the package is corrupted or substituted; abort.
3. Verify the inline signature (§5.30). If verification fails, the
   package's authenticity is unproven; abort.
4. Decompress and parse the tar archive, enforcing the layout rules of
   §5.12, the determinism rules of §5.11 and the detached-signature
   rules of §5.16.
5. Read `.peipkg/manifest.json` and verify it against §5.18.
6. Read `.peipkg/files.json` and verify it against §5.25, including the
   two-way coverage check and the `size_installed` equality of §5.18.
7. For each payload entry, compute its content hash and compare it
   against the files manifest. If any file's hash does not match, abort.
8. Compare the manifest against the index entry that led here (§5.32).
   If any field disagrees, abort.

A consumer MUST NOT install any payload before all eight steps complete
successfully. Partial installation after a verification failure leaves
the system indeterminate and is forbidden.

## Ordering is logical, not temporal

A consumer MAY compute the hashes for steps 1, 3, and 7 in a single
streaming pass: feeding the compressed bytes simultaneously through a
hasher and a decompressor, piping the decompressed bytes through a
second hasher up to the signature entry, and hashing each file's content
as the tar walk reaches it.

What the ordering requires is that no payload is committed to its final
install path, and no decompressed byte is made visible outside the
consumer's own private state, until every step has completed.

## Nothing observable before step 3

A consumer MUST NOT make any decompressed payload byte visible to
another process — including through a staging directory reachable from
outside the consumer's own process tree — before signature verification
has succeeded.

Streaming decompression and hashing are permitted. Observable filesystem
effects are not.

## Verifying the whole transaction first

When a consumer installs several packages together, it MUST complete
steps 1 through 8 for **every** package before extracting **any**
package's payload, and it MUST do so across every installation root the
operation touches.

> [!NOTE]
> This closes a class of multi-package attack: package A is verified,
> extracted, and its contents then influence the verification or
> extraction of package B — A installs a tool B's extraction invokes, or
> A creates a directory whose descriptor decides where B's files land.
> Verifying everything first means extraction operates on a known-good
> set of payloads. The rule binds across roots as well as within one,
> because a package extracted into one root is just as present on the
> filesystem as one extracted into another.

## Committing a payload

A consumer MUST resolve every path component of an install location
relative to a verified parent-directory file descriptor, without
traversing any symbolic link — including one the consumer itself created
earlier in the same operation. A resolution that would traverse a
symlink MUST abort the operation.

A pre-existing symlink at an install path MUST be removed atomically
before the write, and MUST NOT be followed.

A well-formed package never contains a payload entry whose ancestor
component is a symlink. A resolution failure therefore indicates a
malformed or hostile package, or hostile filesystem state.

On Linux this is achieved with `openat2(..., RESOLVE_NO_SYMLINKS)`
anchored at the relevant permitted top-level destination (§5.14), or
with equivalent semantics using `O_NOFOLLOW` on every component against
a carried directory descriptor. A consumer SHOULD additionally apply
`RESOLVE_BENEATH`, `RESOLVE_NO_XDEV`, and `RESOLVE_NO_MAGICLINKS` as
defence in depth, and SHOULD commit a staged file with `renameat2`
against the same pinned parent descriptor rather than a re-walked path
string.

> [!NOTE]
> The format's symlink-target rules (§5.17) are the first layer of the
> defence and this is the second, and neither is sufficient alone. The
> format forbids a symlink whose target resolves outside the managed
> tree; component-wise resolution ensures that even an in-tree symlink —
> or one already on the filesystem before this package arrived — cannot
> redirect a write. Without the second layer, a package shipping a
> symlink in one transaction and a file *under* that symlink in the next
> silently writes outside where it claims to, with no race required.

---
title: Symlinks
description: Symlinks as first-class payload entries — target constraints, cross-package targets, how they are covered by integrity, and their descriptors.
---

Symlinks are first-class payload entries. The tar entry's linkname is
the symlink target.

## Target constraints

A symlink target MUST be a relative path.

A symlink target MUST resolve, when joined with the symlink's parent
directory, to a path that is either within the package's own payload
tree or under one of the permitted top-level install destinations of
§5.14. An absolute target is forbidden, as is a target whose resolution
escapes those destinations entirely.

A symlink target is subject to the same path-validity constraints as a
payload path (§5.13): valid UTF-8, no NUL bytes, no ASCII control
characters, no backslashes, NFC normalisation, and the length limits.

A consumer MUST validate every symlink target against these constraints
before extracting the entry. A package containing a non-conforming
symlink target MUST be rejected.

> [!NOTE]
> Format-level validation cannot distinguish a symlink whose resolved
> target is an installable path that no package actually installs. A
> target reached by `..` traversal into a permitted destination passes
> validation and produces a dangling symlink; one that would overwrite
> an existing owned file is caught by the one-package-per-path rule
> (§5.16). Both are consumer-side outcomes, not format errors.

## Cross-package targets

A producer MAY emit a symlink whose target resolves into a different
package's payload tree, provided the resolved path is under a permitted
destination. The canonical case is the conventional library split, where
a `-dev` package ships a developer link (`libfoo.so`) whose target
(`libfoo.so.1`) lives in the corresponding runtime package.

A producer SHOULD declare the target's owning package as a dependency,
so that the target is present at extraction time. The format does not
record this relationship at the symlink level; it is captured at the
package level through `dependencies` (§5.21).

> [!NOTE]
> Prohibiting cross-package symlinks was considered — it would have
> forced restructured `-dev` splits with developer links living in
> runtime packages — and rejected. Forbidding them deviates from
> universal Linux convention with no corresponding security gain: the
> defence below operates on resolved-target validity, not on whether the
> resolution crosses a package boundary.

## Integrity

A symlink has no content body, and so is not hashed in the files
manifest (§5.25). Its target is integrity-checked directly: the linkname
stored in the tar header is what the consumer compares, and that header
is inside the signed bytes (§5.28).

## Security descriptors

A symlink does not carry an independent security descriptor. Access to a
symlink is governed by access to its target. A security descriptor
override (§5.20) MUST NOT target a symlink entry.

> [!NOTE]
> The classic symlink TOCTOU attack — install `/usr/share/foo` as a
> symlink to a system file, then have a later write at
> `/usr/share/foo/bar` traverse it — is prevented in two layers. The
> format forbids symlink targets resolving outside the managed tree, and
> extraction resolves every path component without following a symlink,
> so even an in-tree symlink cannot redirect a later write.

---
title: Type Conflicts
description: Two strata holding one name with different types — the provider's type wins, masking is total, and the result is stable.
---

Two strata may hold the same name with different types — a directory in
one, a regular file in another. The provider's type is the type of the
resolved object, and the outer inode is given the provider's mode and
the operations tables that follow from it. [*resolution.conflict-provider-type-wins]

- Where the provider is a **directory**, lower-precedence strata that
  hold the name as a directory participate in a merged directory
  (§4.3.2). Lower-precedence strata that hold the name as anything else
  are masked. [*resolution.conflict-directory-merges-only-directories]
- Where the provider is **not** a directory, every lower-precedence
  entry of that name is masked, whatever its type. [*resolution.non-directory-masks-lower] Only the provider's
  path is retained on the dentry; the other strata's references are
  released as soon as the provider is chosen.

## Masking is total

A masked entry is unreachable through the mount. Where the masked entry
is a directory, its entire subtree is unreachable: no path beneath the
masked name resolves, regardless of what the masked directory contains
and regardless of whether some other stratum holds part of that
subtree. [*resolution.masking-hides-whole-subtree]

This is enforced by the ancestor pass described in §4.3.1. Each proper
prefix of a relative path is resolved across every stratum and its
merged provider computed; a prefix whose merged provider is not a
directory returns `ENOTDIR` before the final component is considered.
Because the test uses the merged answer rather than a per-stratum one,
another stratum holding the subtree cannot rescue it. [*resolution.masked-subtree-not-rescued-by-lower-stratum]

A regular file at `/x` in a high-precedence stratum therefore hides a
whole `/x/…` tree in a lower one. That is severe, and deliberate: the
alternative — resolving `/x` as a file but `/x/y` through the masked
directory — would make a path's meaning depend on how far along it the
caller looked.

Masking modifies nothing. Resolution and enumeration are read-only
throughout, no marker is written to any stratum, and the masked entry
remains present and unchanged in its own stratum, reachable by any path
that does not traverse the mount. [*resolution.masking-writes-nothing]

## Stability

Type conflicts resolve identically for every caller and every
operation, because provider selection is a pure function of the
presence bitmap and consults neither.

An operation that would only be valid against the masked type does not
cause the masked entry to be selected. It fails against the provider
instead, with whatever error that type produces — typically `ENOTDIR`
from the ancestor pass, or `EISDIR` raised by the generic VFS against
an outer inode carrying the provider's mode. [*resolution.conflict-operation-fails-against-provider]

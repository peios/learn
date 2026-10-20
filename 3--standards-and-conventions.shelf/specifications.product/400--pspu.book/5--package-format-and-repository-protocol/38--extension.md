---
title: Extension
description: What may be added to these documents without a version bump, what may not, the reserved space, and how deprecation works.
---

Every document in this chapter carries a `schema_version`, currently 1.
A change that a conforming implementation of this version cannot process
correctly requires a version bump; a change it can safely ignore does
not.

## Additive changes

The following are additive and do **not** require a version bump:

- A new optional field in the manifest, an index entry, or the
  repository descriptor. A consumer ignores it (§5.9).
- A new optional metadata entry under `.peipkg/` (§5.12). A consumer
  ignores it, and its presence MUST NOT prevent installation.
- A new sibling artifact alongside a package file (§5.36).

A producer emitting an additive extension MUST ensure that a consumer
ignoring it still behaves correctly. An extension whose omission changes
what gets installed is not additive.

## Changes requiring a version bump

- Adding, removing, or changing the meaning of a **required** field.
- Adding a value to a closed enumeration: the side-effect identifiers of
  §5.24, the architecture identifiers of §5.8, the hash algorithms of
  §5.25, the signature algorithms of §5.28, the key statuses of §5.32,
  the index kinds, the constraint operators of §5.7, the licence classes
  of §5.18, or the signature policies of §5.37. A conforming implementation of this version MUST
  reject a value outside each of those sets, so a new value is not
  ignorable.
- Any change to the version comparison algorithm of §5.6, which is
  frozen.
- Any change to the determinism rules of §5.11, which decide the bytes.
- Any change to the signature envelope of §5.28, which is strictly
  parsed by construction.

## Reserved space

This version reserves syntactic room in three places, so that a future
extension can be additive where it would otherwise not be:

- The `algorithm` fields of the files manifest and the index hash object
  reserve room for a further hash algorithm.
- The `arch` qualifier on a dependency reserves room for explicit
  architecture identifiers, for a multi-architecture system.
- The sibling-artifact paths of §5.36 reserve room for build
  attestations and bills of material.

An implementation of this version MUST reject a value in a reserved
space rather than guess at it.

## Deprecation

A field this specification requires MUST NOT be removed within a
`schema_version`. When a field becomes unnecessary, a producer continues
emitting it and a future version removes it under a new
`schema_version`.

---
title: Package Identity
description: How a package is named by the hash of its manifest, what a ref records, and why a version, once stored, never changes.
---

## Identity

A package's **identity** is the identity of its manifest's bytes (§5.9):
`sha256:` and the SHA-256 hash of the manifest. The manifest lists every
path of the package with the hash of each file's content (§5.18), so the
identity covers every byte and every piece of metadata the package has.

Two packages with the same identity are the same package.

## Refs

A **ref**, `refs/<name>/<version>/<arch>`, records which package an
artifact directory holds for that package ID: its identity, then a newline,
and nothing else.

A consumer MUST refuse a ref that holds anything else, and MUST check that
the manifest it names hashes to that identity and names that package ID.

## A version is never replaced

Once an artifact directory holds a package at a version, it MUST NOT come
to hold another package at that version. Packing or fetching a package
whose ID is held with another identity MUST fail, writing nothing. A change
to a package is a new revision (§5.5).

A bootstrap, whose artifact directory nothing has fetched from yet, MAY
replace a package, with an explicit request naming it. The manifest it
replaces and that manifest's blobs stay.

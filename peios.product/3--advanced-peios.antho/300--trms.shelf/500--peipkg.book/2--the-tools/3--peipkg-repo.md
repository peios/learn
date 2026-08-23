---
title: peipkg-repo
description: The tool that serves a repository — its verbs, what publishing verifies, the invariants it defends, and what it does not do.
---

`peipkg-repo` is the publisher: it maintains the static file tree a
repository serves.

## Verbs

| Verb | Effect |
|---|---|
| `init` | Establish a new repository tree, with a descriptor and empty indexes |
| `publish` | Ingest one or more package files, derive both indexes, and sign everything |
| `verify` | Check a published tree for internal consistency |

## What publishing does

Publishing verifies each incoming package in full — archive structure,
manifest, files manifest, per-file hashes, and its signature against the
repository's own keys — before it derives anything from it. Index
entries are then extracted directly from each verified manifest, never
from operator input.

Both indexes are rewritten on every publication and both are stamped
with the same `index_version` and `generated_at`. The new version is one
greater than the highest either index carried, so the pair advances
together and a consumer holding one has a usable freshness floor for the
other.

## Invariants it defends

`init` refuses to run in a non-empty directory. Establishing a fresh
repository at `index_version` 1 over an existing one would look to every
consumer like an unrecoverable rollback.

`publish` refuses to re-publish a name, version, and architecture that
already exists. That is the retention guarantee of PSPU §5.35 enforced
at the point where it could be broken.

`publish` refuses a URL template that cannot distinguish one version
from another, because such a template makes retention unkeepable: the
second version published would overwrite the first.

Deriving the active index from the archive is a projection to the
highest version per name. When two architectures of one package tie on
version, the publisher stops with an error rather than choosing — a
repository that silently picked one would advertise a different package
than its operator intended.

## What it does not do

There is no verb for rotating a signing key or marking one revoked.
Changing a descriptor's key list means editing `repo.json` and re-signing
it by other means.

Publishing does not check a package's payload against the install-layout
rules. A package whose payload lands outside the permitted destinations
can be published and served; every consumer refuses it at install time
instead.

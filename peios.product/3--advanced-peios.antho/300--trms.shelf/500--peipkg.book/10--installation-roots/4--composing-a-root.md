---
title: Composing a Root
description: Building a fresh root deterministically without touching the host or running package code — the manifest, the lock, and the three phases.
---

`peipkg-compose` builds a populated root from nothing: offline,
deterministically, without touching the host filesystem and without
executing any package's code. It is the counterpart to peipkg, which
mutates a live system.

It is not an image builder. An outer tool calls compose, then chroots to
pack the initramfs, squashes the root, and builds the boot image.

## The manifest

A TOML document with a schema version, declaring:

| Key | Meaning |
|---|---|
| `arch` | The primary architecture, which becomes the composed database's recorded value |
| `source_date` | The timestamp everything is stamped with |
| `local_packages` | Globs of package files on the build host that join the candidate set — the bootstrap path |
| `[[repository]]` | Name, base URL, priority, signature policy, trust anchors, transport allowance, minimum index version |
| `[[root]]` | A name and a path, declaring a named root nested inside the output |
| `[[package]]` | A name, an optional version constraint, an optional repository pin, an optional root |

Unknown keys anywhere are rejected. A package pinning an undeclared
repository, or placed in an undeclared root, is an error. Package
identity is (root, name), so the same package may be requested in two
roots.

## The lock

Resolution writes a lock: the pinned closure, with each package's
source, absolute URL, hash, root, and the compressed and installed sizes
its repository index advertised. It carries a digest of the manifest, so
that building against a stale lock is caught.

The lock also records, per repository the closure draws from, that
repository's signature policy and the trust set resolution established
for it — each key's fingerprint, public bytes, status, and any expiry.
Trust is established once, at resolve time; recording it is what lets
the build phase verify signatures without repeating the ceremony. A lock
naming a repository package whose source it records no trust state for
is rejected as malformed.

The digest covers the packages, their constraints, their repository
pins, the `[[root]]` declarations and each package's root placement —
everything that influences resolution. Moving a package between roots,
or changing where a root lives, changes the digest, so a build refuses
the stale lock rather than silently reproducing the previous
placement.

The lock's `root` key is a **path** relative to the output, while the
manifest's `root` key of the same name is a **name**. A lock is
therefore bound to one root layout.

## The three phases

**Resolve** performs the full trust ceremony for each declared
repository in a throwaway database that never reaches the output,
fetches the active index — and the archive index when a constraint might
need historical versions — and reads any local package files into
synthetic candidates. Manifest pins filter the candidate set. Resolution
then runs against an **empty installed set**.

Elevated actions the plan implies are printed as warnings and the build
proceeds, because compose runs unattended with nobody to authorise them.

**Fetch** downloads every package within the bound the lock's
`size_compressed` sets, checks its bytes against the hash the lock
recorded, verifies its inline signature against the trust set the lock
carries for its source, validates its format, and cross-checks the
archive's own manifest against the lock entry. Every package is verified
before any is extracted.

Signature verification applies the source's recorded policy: under
`required` an unsigned package is refused, and under either policy a
signature made by a key the repository has since marked **revoked**, or
by a transitioning key past its expiry, is refused as well. Key status is
evaluated against the clock at build time, not at lock time, so a key
revoked after the lock was written stops verifying — a build from an
unchanged lock can begin to fail, and that is the intent.

Decompression is bounded by the `size_installed` the lock carries from
the index, and the archive's manifest must declare the same figure. The
manifest is inside the stream being bounded, so it cannot supply the
bound.

**Assemble** buckets packages by root and, per root, validates the
payload layout against the fetched bytes, resolves claims, seeds the
database, extracts payloads, and materialises claim links. The whole
tree is built under a temporary name and renamed into place on success.

## What it seeds

Into each root's database, in one transaction: the recorded
architecture, a package row per package carrying the verbatim manifest,
an owned-file row per payload entry, claim holder and link rows, and the
named-root registrations.

Owned-file rows are written *before* any file is extracted, so a
cross-package path collision aborts the build before anything lands.

Journal rows are deliberately left empty: a composed root has no
transaction history because nothing was ever applied to it
incrementally.

## What it writes that no package owns

Two things: a repository configuration file for each declared
repository, and a license inventory naming every composed package's
license and provenance.

Neither appears in the owned-file table, so neither is upgradable or
verifiable by peipkg afterwards. Both land under paths a package could
not install to.

## What it deliberately omits

No side effects — a composed root's library cache, module dependency
cache, and man index are never built. No security descriptor
materialisation. No audit events. No repository trust state or index
cache in the output, so the composed system performs its own trust
ceremony on first use. The trust state the lock carries is an input to
the build, not something the build writes into the root.

## Layout enforcement

The permitted-destination check runs at compose time, against the
fetched bytes rather than the producer's word for them, and the
two-key rule applies exactly as it does at install: a package declaring
itself a special system package composes only when the composition also
grants the bypass, and a declaration without the grant produces an
explanatory refusal.

## Root-level views

The composer synthesises no root-level runtime view. It creates payload
entries, claim links, the repository configuration, and the license
inventory, and nothing else. Where a boot root needs the psABI-fixed
interpreter path to reach the loader before any view is mounted, that
mapping is ordinary package payload from the base-filesystem package —
shipped for each independent boot root, including the initramfs — rather
than something the composer invents.

## Roots with nothing in them

A declared root that no package is placed in is created anyway, with its
own database holding nothing. A declared empty root is a reasonable
thing to want — somewhere to install into later — and the alternative,
registering a root whose directory does not exist, made `--root <name>`
on the composed system fail when peipkg tried to open its database.

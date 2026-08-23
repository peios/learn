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
source, absolute URL, hash, and root. It carries a digest of the
manifest, so that building against a stale lock is caught.

The digest covers the packages, their constraints, and their repository
pins. It does not cover root declarations or per-package root placement,
so a manifest edit that only moves a package between roots, or changes
where a root lives, produces the same digest — and a build without an
explicit update silently reproduces the previous placement.

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

**Fetch** downloads every package, checks its bytes against the hash the
lock recorded, validates its format, and cross-checks the archive's own
manifest against the lock entry. Every package is verified before any is
extracted.

What is not checked is the inline signature against a trust set. The
resolve phase performs the trust ceremony and then discards the trust
state with the temporary database it was built in, so the build phase
has hashes but no keys. The chain that remains is: the index was signed,
the lock records the index's hash, the bytes match the hash. A package
whose signing key has since been **revoked** is accepted by that chain
and refused by peipkg.

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
ceremony on first use.

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

A declared root that no package is placed in is registered but never
created. The registration points at a directory that does not exist, and
addressing that root on the composed system fails when peipkg tries to
open its database.

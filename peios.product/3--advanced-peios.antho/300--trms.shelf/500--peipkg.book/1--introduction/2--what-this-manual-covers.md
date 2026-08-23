---
title: What This Manual Covers
description: The scope of this manual — the package manager, the producer toolchain and the image composer — and what is documented elsewhere.
---

This manual describes peipkg as it is built: the package manager, the
producer toolchain that feeds it, the image composer that shares its
machinery, and the repository publisher.

## Covered here

- The programs and where their state lives (chapter 2)
- Repository configuration, trust, and refresh (chapter 3)
- Dependency resolution: satisfaction, candidate selection, and failure
  (chapter 4)
- Installation: validation, staging, extraction, and registration
  (chapter 5)
- Upgrade and removal, and how configuration files survive them
  (chapter 6)
- Transactions: the lock, the journal, the commit, and crash recovery
  (chapter 7)
- Rollback and recovery from an interrupted or failed operation
  (chapter 8)
- Roles and claims (chapter 9)
- Installation roots and image composition (chapter 10)
- Side effects (chapter 11)
- Producing packages with pekit (chapter 12)
- The security model: privilege, audit, and operator authorisation
  (chapter 13)
- What goes wrong and what it looks like (chapter 14)

## Covered elsewhere

The **package format and the repository protocol** are specified in
PSPU §5 and are not restated here. Anything a third party has to reproduce
exactly — the container layout, the manifest schema, version comparison,
the payload rules, the signature construction, the index schemas, the
freshness rules — lives there. This manual describes what peipkg does
with those artifacts, and cites the specification rather than
paraphrasing it.

**Security descriptors and the access-check model** belong to the
kernel's access-control subsystem and are documented with it. peipkg
supplies descriptor bytes at file-creation time and never interprets
them.

**Roles, role features, core features, and applets** are separate
subsystems that reference packages. A package is a distribution
primitive beneath them.

**Service definitions, registry seeds, and reconciller manifests** are
integration metadata belonging to the artifacts that compose packages,
not to packages.

---
title: Scope and Roles
description: What this chapter specifies — the .peipkg artifact and the repository protocol that serves it — its roles, and what it leaves out.
---

This chapter specifies the **peipkg package format** and the **peipkg
repository protocol**: the artifact by which compiled software is
distributed to a Peios system, and the static-HTTP protocol by which a
system discovers, trusts, and fetches those artifacts.

A package is the binary distribution primitive of Peios — the unit of
build, distribution, and trust. It is deliberately narrow: it defines
how binaries reach a system, not how they are integrated into services,
roles, or features. Higher-level artifacts reference packages; a package
knows nothing of them.

## Roles

Three roles speak this specification. A requirement is stated against
the role, not the program; one program may serve more than one.

| Role | Obligation |
|---|---|
| **Producer** | Builds package files. Everything a `.peipkg` contains is a producer obligation. |
| **Repository** | Publishes a descriptor, two indexes, and package files over static HTTP, and signs the metadata. |
| **Consumer** | Fetches, verifies, and installs packages. Every validation and rejection rule binds the consumer. |

A repository operator is usually also a producer, but need not be: a
repository may publish packages built elsewhere, and the format's
signatures survive the journey.

## In scope

- The on-wire package file: container, internal layout, manifest
  schema, payload layout, per-file integrity
- Package identity: names, versions, version comparison, architectures
- How a package expresses its relationships to other packages, and what
  it means for one to satisfy another
- Package signing: algorithm, envelope, verification
- The repository protocol: descriptor, active and archive indexes, URL
  conventions, freshness and rollback protection
- Establishing and maintaining trust in a repository
- The rules under which the format may be extended

## Out of scope

- **How a consumer decides what to install.** Given several candidates
  that all satisfy a dependency, which one it picks, in what order it
  applies a plan, and how it recovers from an interrupted one are the
  consumer's own design.
- **How a consumer stores its state.** The installed-package database,
  its transaction journal, and its cache format are private.
- **How a producer builds a package.** Recipes, build farms, and source
  trees are producer mechanics; only their output is specified here.
- **Roles, role features, core features, and applets.** These are
  separate subsystems that reference packages.
- **Integration metadata attached to packages** — service definitions,
  registry seeds, reconciller manifests. These belong to the artifacts
  that compose packages, not to packages.
- **Security descriptor semantics.** A package carries security
  descriptor bytes; what they mean is specified with the kernel's
  access-control subsystem.

## Relationship to other chapters

Nothing in this chapter is a conformance requirement on a Peios system:
a system that ships software some other way is still Peios (§1.1). What
this chapter guarantees is that the format and the protocol are written
down and will not move.

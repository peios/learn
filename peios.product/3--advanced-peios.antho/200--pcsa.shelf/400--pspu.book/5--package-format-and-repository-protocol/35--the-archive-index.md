---
title: The Archive Index
description: Every version a repository has ever advertised, its retention and schema, and how it relates to the active index.
---

The archive index lists every version of every package a repository has
ever advertised, including versions superseded by newer releases. It is
the source of historical data for downgrade, version pinning, and
forensic queries.

## Retention

A repository MUST retain every package version it has ever advertised.
Once a package has been published at version V, the repository MUST
continue to make V fetchable indefinitely, and the archive index MUST
continue to list it.

> [!NOTE]
> This is a deliberate departure from rolling-only models. Retention is
> what supports rollback, reproducible deployment, security forensics,
> and long-running systems held at an older version.

A repository MAY retire pre-release or development versions under a
stated retention policy. Retirement MUST NOT silently remove a package a
consumer might be using, and SHOULD be coordinated with consumer notice.

A pruned package MUST also be removed from the repository's package
storage: the archive index MUST NOT reference a package file that is no
longer fetchable.

> [!NOTE]
> Reasonable policies include retaining all stable releases
> indefinitely, retaining pre-releases for a year after each successor,
> or never pruning anything. This specification neither mandates nor
> forbids pruning.

## Location and signing

The archive index's URL and its detached signature's URL are declared by
the descriptor (§5.31). It MUST be signed under the same rules as the
active index (§5.33).

## Schema

The top-level schema is identical to the active index (§5.33), except:

- `kind` MUST be `archive`;
- the `packages` array MAY contain several entries with the same `name`,
  at different versions.

The per-package entry schema is identical. Each historical version
contributes one entry.

`index_version` semantics are identical, and every freshness and
rollback requirement of §5.34 applies to the archive index exactly as it
does to the active one.

## Ordering

The `packages` array MUST be sorted lexicographically first by `name`,
then within a name by `version` **descending** per §5.6. The first entry
for any name is its highest version; subsequent entries for that name
are progressively older.

Where two entries of one name share a version — differing only in
architecture — the ordering between them MUST be total and MUST be
stated by the producer's tooling, so that the file is reproducible.

> [!NOTE]
> Highest-first ordering puts the most recently shipped version of each
> package at the top of its name group, so a consumer scanning for the
> latest version satisfying a constraint can stop as soon as the
> constraint is satisfied or exceeded.

## Relationship to the active index

For every entry in the active index there MUST be at least one entry in
the archive index with the same `name`, `version`, `architecture`, and
`hash`. The archive index is a superset of the active index.

Equivalently: the active index is the per-name maximum projection of the
archive index, where "maximum" is the highest version per name under
§5.6.

A repository publishing both indexes SHOULD publish them at the same
`index_version` and `generated_at`, so that a consumer holding one has a
usable floor for the other.

## Fetch frequency

The archive index is large compared to the active index — potentially
many megabytes for a long-running repository. A consumer SHOULD fetch it
only when it is needed: for a historical query, for a pin or a
downgrade, or when its cached copy expires. A routine sync SHOULD fetch
only the active index.

A consumer SHOULD cache the archive index aggressively, since it changes
only when a version is published or pruned.

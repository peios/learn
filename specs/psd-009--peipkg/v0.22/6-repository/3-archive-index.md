---
title: Archive Index
---

The archive index lists every version of every package the
repository has ever advertised, including versions
superseded by newer releases. It is the source of historical
package data for downgrade, version pinning, and forensic
queries.

## Retention model

A repository MUST retain every package version it has ever
advertised. Once a package has been published with version
V, the repository MUST continue to make package V fetchable
indefinitely. The archive index MUST continue to list V.

> [!INFORMATIVE]
> This is a deliberate departure from rolling-only models
> (e.g., Arch). The retention requirement supports rollback,
> reproducible deployments, security forensics, and
> long-running systems on legacy versions.

A repository MAY retire pre-release or development versions
under operator-defined retention policy. Retirement MUST NOT
silently remove packages a consumer might be using; it
SHOULD be coordinated with consumer notice.

## URL and signing

The archive index URL is declared by the repository
descriptor's `indexes.archive.url` field (§6.1.5). The
detached signature URL is declared by
`indexes.archive.signature_url`.

The archive index MUST be signed under the same rules as
the active index (§6.2.1).

## Top-level schema

```json
{
  "schema_version": 1,
  "repo": "<string>",
  "kind": "archive",
  "generated_at": "<RFC 3339 timestamp>",
  "packages": [<package_entry>...]
}
```

The schema is identical to the active index (§6.2.2)
except:

- `kind` MUST be `archive`.
- The `packages` array MAY contain multiple entries with
  the same `name` (different `version`).
- `index_version` semantics are identical: monotonically
  increasing per publication, consumer enforces non-
  decreasing on refresh.

## Package entry schema

The per-package entry schema is identical to the active
index (§6.2.3). Each historical version contributes one
entry.

## Ordering

The `packages` array MUST be sorted lexicographically,
first by `name` and then within name by `version`
descending (per §2.2.6). The first entry for any given
name is the highest version; subsequent entries for that
name are progressively older.

> [!INFORMATIVE]
> Highest-version-first ordering puts the most-recently-
> shipped version of each package at the top of its name
> group. A consumer scanning for "latest pre-release" or
> "version satisfying constraint X" can stop scanning a
> name group as soon as the constraint is satisfied or
> exceeded.

## Relationship to the active index

For every entry in the active index, there MUST be at least
one entry in the archive index with the same `name`,
`version`, `architecture`, and `hash`.

The archive index is a superset of the active index.

> [!INFORMATIVE]
> An equivalent way to describe the relationship: the active
> index is the per-name maximum projection of the archive
> index, where "maximum" is the highest version per name
> per the comparison rules (§2.2.6).

## Fetch frequency

The archive index is large compared to the active index
(potentially many megabytes for a long-running
repository). Consumers SHOULD fetch the archive index only
when needed:

- When a user explicitly queries historical versions
- When a user pins to or downgrades to a non-current
  version
- When the consumer's caching policy expires the cached
  copy

Routine `pkg sync` operations SHOULD fetch only the active
index, not the archive index.

## Pruning of pre-releases

A repository MAY prune pre-release versions older than a
declared age threshold from the archive index, provided
that pruning is documented and consumers are advised. This
specification does not mandate or forbid such pruning;
operators choose retention policy based on their use case.

> [!INFORMATIVE]
> Reasonable policies might include: retain all stable
> releases indefinitely; retain pre-releases for one year
> after each successor; never prune anything.

A pruned package MUST also be removed from the
repository's package storage; the archive index MUST NOT
reference packages whose `.peipkg` files are no longer
fetchable.

## Size

For a repository of approximately 300 packages with
approximately 20 versions retained per package, the archive
index is on the order of 2-3 MB compressed and 12-18 MB
uncompressed. Consumers SHOULD fetch with HTTP-level
compression when available, and SHOULD cache the archive
index aggressively (it changes only when new versions are
published or old versions are pruned).

---
title: The Active Index
description: The index listing the current version of every advertised package — its schema, entries, derivation rule, and deliberate omissions.
---

The active index lists the current version of every package a repository
advertises. It is the index a consumer fetches on a routine sync.

## Location and signing

The active index's URL and its detached signature's URL are declared by
the descriptor (§5.31).

The index MUST be accompanied by a detached signature: a signature
envelope (§5.28) over the SHA-256 digest of the index file's exact
bytes. The signing key MUST be one of the descriptor's keys with status
`active` or `transitioning`.

A repository configured to permit unsigned content MAY publish the
active index unsigned.

> [!NOTE]
> Detached metadata signatures and package signatures share a single
> construction — an envelope over a SHA-256 digest — so a verifier
> implements it once. The digest indirection is free for a small JSON
> index and lets a multi-gigabyte package be verified in one streaming
> pass.

## Schema

```json
{
  "schema_version": 1,
  "repo": "<string>",
  "kind": "active",
  "index_version": <integer>,
  "generated_at": "<RFC 3339 timestamp>",
  "packages": [<package_entry>...]
}
```

| Field | Description |
|---|---|
| `schema_version` | MUST be 1 in this version. |
| `repo` | The repository's name, matching `repo.name` in the descriptor. |
| `kind` | MUST be `active`. |
| `index_version` | A monotonically increasing positive integer identifying this index revision (§5.34). |
| `generated_at` | RFC 3339 UTC timestamp of generation. |
| `packages` | One entry per package currently advertised. |

A consumer MUST verify that `repo` matches the descriptor's `repo.name`
and that `kind` matches the index it requested. An archive index served
in place of an active one MUST be rejected.

## Package entries

```json
{
  "name": "<string>",
  "version": "<string>",
  "architecture": "<string>",
  "description": "<string>",
  "license": "<string>",
  "homepage": "<string>",
  "default_root": "<root reference>",
  "dependencies": [<dependency>...],
  "optional_dependencies": [<dependency>...],
  "conflicts": [<dependency>...],
  "provides": [<provides>...],
  "replaces": [<replaces>...],
  "side_effects": [<string>...],
  "size_compressed": <integer>,
  "size_installed": <integer>,
  "hash": { "algorithm": "<string>", "value": "<hex string>" },
  "url": "<string>",
  "build": { "timestamp": "<RFC 3339>", "farm_id": "<string>" }
}
```

An entry MUST contain `name`, `version`, `architecture`,
`dependencies`, `conflicts`, `provides`, `replaces`, `side_effects`,
`size_compressed`, `size_installed`, `hash`, and `url`. The array fields
MUST be present even when empty, emitted as `[]`. The remaining fields
are RECOMMENDED and MAY be omitted.

`name`, `version`, and `architecture` MUST each be validated against
§5.3, §5.5, and §5.8 respectively on parse — with the same strictness a
manifest receives. An index is fetched from the network and its values
flow into URL construction and into the consumer's own records.

`size_compressed` and `size_installed` are required because they are the
input to the decompression bound of §5.27.

`hash` carries `algorithm`, which MUST be `sha256` in this version, and
`value`, the lowercase hexadecimal SHA-256 of the `.peipkg` file in its
compressed on-wire form.

## The derivation rule

The active index is a **derived view** of the packages it advertises.
Every field of an entry MUST exactly match the corresponding field of
that package's manifest where one exists, and MUST exactly match the
properties of the actual package file for `hash`, `size_compressed`, and
`url`.

Tooling generating an index MUST extract values directly from package
manifests. Editing an index by hand is forbidden.

Where a manifest contradicts an index entry, the manifest is
authoritative (§5.18) — and the contradiction is a defect in the
repository, not a difference to accommodate. A consumer MUST compare the
downloaded package's manifest against the index entry that led to it,
across **every** field the index carries, and MUST reject the package on
any mismatch (§5.26 step 8).

> [!NOTE]
> Comparing only name, version, and architecture is not enough, and the
> gap is not theoretical. A consumer builds its entire dependency and
> conflict graph from index claims. A repository that publishes an entry
> declaring no `conflicts` for a package whose manifest declares one
> against a critical installed package gets a plan computed on the lie,
> approved by the operator on that basis, and applied — with the real
> relations discovered by nobody. The index is a convenience for
> planning without downloading; it is not a second source of truth.

## Deliberate omissions

The index omits three manifest fields:

- `sd_overrides` — not relevant to planning, and potentially large.
- `build.source_ref` — long and low in information density; consult the
  package when it is wanted.
- the manifest's own `schema_version` — the index carries its own.

These remain in the manifest and are available to a consumer that
fetches the package. Because they are omitted rather than mismatched,
they are outside the comparison above.

## URLs

`url` declares where the package file is fetched from, and MAY be
relative or absolute (§5.36). The conventional form is relative:

```
"url": "/p/nginx/1.26.2-3/nginx_1.26.2-3_x86_64.peipkg"
```

This keeps an index portable: the same file is valid at any
`<repo-base>` hosting the same package files.

## Ordering

The `packages` array MUST be sorted lexicographically by `name`. Two
entries with the same `name` in an active index are invalid: each name
appears exactly once.

> [!NOTE]
> Per-name uniqueness is what makes the index "active" — one current
> version of each package. The archive index (§5.35) relaxes exactly
> this constraint and nothing else.

## Unknown fields

A consumer MUST ignore unknown fields, at the top level and per package,
per §5.9. A producer MAY emit additional fields in a future schema
version.

The exception is a field whose meaning is critical to correctness, such
as a hash algorithm identifier. Such changes are expected to arrive
through a `schema_version` bump, not as a silent addition.

## Size and caching

For a repository of a few hundred packages the active index is on the
order of 100 KB compressed. A consumer SHOULD fetch with HTTP-level
compression where it is offered, and SHOULD cache the parsed index
between invocations: the index changes only when the repository
publishes, which is far less often than a consumer reads.

A cached index MUST be stored under a security descriptor granting write
access only to the principal permitted to install packages.

A consumer MUST re-verify a cached index's signature on **every**
operation that relies on it, rather than trusting its cached state
across operations. Caching avoids re-parsing; it does not avoid
re-verifying.

A consumer SHOULD additionally cross-check a cached index against its
own recorded freshness state (§5.34), and reject a cached index whose
`index_version` or `generated_at` disagrees with what it recorded.

> [!NOTE]
> Without re-verification, whoever can write to the cache can substitute
> metadata between the cache write and the next read. Re-verifying on
> every use closes that race, and the cost is negligible: verifying a
> signature over a few hundred kilobytes is sub-millisecond. The
> cross-check against recorded state closes the matching hole, where an
> attacker substitutes an older *validly signed* index directly into the
> cache, bypassing the refresh path where §5.34's floor is enforced.

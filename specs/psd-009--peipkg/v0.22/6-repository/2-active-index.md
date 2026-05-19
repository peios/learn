---
title: Active Index
---

The active index lists the current version of every
package the repository currently advertises. It is the
default index a consumer fetches on routine sync
operations.

## URL and signing

The active index URL is declared by the repository
descriptor's `indexes.active.url` field (§6.1.5). The
detached signature URL is declared by
`indexes.active.signature_url`.

The active index MUST be accompanied by a detached
signature published at the `indexes.active.signature_url`
declared in the descriptor. The signature is over the
index file's exact bytes, encoded as Ed25519 base64
(RFC 4648 §4) without padding — the same detached-
signature convention as the repository descriptor
(§6.1.6). The signing key MUST be one of the keys listed
in the descriptor with status `active` or `transitioning`.

> [!INFORMATIVE]
> The index, like the descriptor, is a small JSON document
> verified in full before use, so its signature is over
> the raw file bytes. A package signature (§5.3) instead
> signs a SHA-256 of the payload, so that a multi-gigabyte
> package can be verified in a single streaming pass; that
> reason does not apply to an index.

A repository configured to permit unsigned content (§6.5.3)
MAY publish the active index unsigned.

## Top-level schema

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

| Field | Type | Description |
|---|---|---|
| `schema_version` | integer | MUST be 1 in this specification. |
| `repo` | string | The repository's name, matching `repo.name` from the descriptor (§6.1.2). |
| `kind` | string | MUST be `active` in this index. |
| `index_version` | integer | Monotonically-increasing positive integer identifying this index revision (see §6.2.3). |
| `generated_at` | string | RFC 3339 UTC timestamp of when the index was generated. |
| `packages` | array | One entry per package currently advertised. |

## Freshness and rollback protection

Each new publication of an index MUST set `index_version`
to a value strictly greater than any previously-published
value for the same repository.

A consumer MUST record the highest `index_version` it
has ever observed for each configured repository. On
each refresh, the consumer MUST reject any fetched
index whose `index_version` is less than the recorded
value, even if the index is correctly signed and the
signature key is still trusted.

The consumer MUST also reject any fetched index whose
`generated_at` is older than the recorded
`generated_at` for the previously-trusted index from
the same repository.

The first-add of a repository (§6.5.2) is the bootstrap
of the consumer's recorded `index_version` floor. To
defend against an attacker serving a stale-but-signed
index at first-add, a repository SHOULD distribute a
*minimum acceptable index_version* alongside its
trust-anchor fingerprints (the same out-of-band
distribution mechanism). Consumers SHOULD use this
minimum as the initial recorded floor; if the first-
fetched index has an `index_version` less than the
distributed minimum, the consumer MUST refuse the
repo-add operation.

A refresh that fetches an index whose `index_version`
equals the recorded value AND whose `generated_at`
equals the recorded value is treated as a *failed*
refresh (no progress). The consumer MUST NOT advance
the "last successful refresh" timestamp on such a
fetch. This prevents an attacker from holding a
consumer at the same index indefinitely while the
clock burns past the maximum trusted age.

These checks defend against rollback / freeze attacks:
an attacker who controls a CDN edge or substitutes the
served index cannot replay an older signed index to
hide newer (security-fix) packages from the consumer,
nor can they hold the consumer at a current-but-frozen
state by repeatedly serving the same index.

> [!INFORMATIVE]
> Without `index_version` enforcement, the spec's
> per-package signing and index signing would still
> verify, but the *set* of currently-advertised
> packages could be silently rolled back. This is the
> classic freeze attack from package-manager security
> literature (e.g., TUF). The monotonic `index_version`
> check closes the gap.

A consumer MUST also enforce a maximum freshness
window: an index whose `generated_at` is older than 90
days MUST trigger a refresh attempt before any install
operation proceeds. The 90-day default MAY be tuned by
operator configuration; values greater than 365 days
SHOULD generate a warning each time they are exercised.

## Package entry schema

Each entry in `packages` has the following schema:

```json
{
  "name": "<string>",
  "version": "<string>",
  "architecture": "<string>",
  "description": "<string>",
  "license": "<string>",
  "homepage": "<string>",
  "dependencies": [<dependency>...],
  "optional_dependencies": [<dependency>...],
  "conflicts": [<dependency>...],
  "provides": [<provides>...],
  "replaces": [<replaces>...],
  "side_effects": [<string>...],
  "size_compressed": <integer>,
  "size_installed": <integer>,
  "hash": {
    "algorithm": "<string>",
    "value": "<hex string>"
  },
  "url": "<string>",
  "build": {
    "timestamp": "<RFC 3339 timestamp>",
    "farm_id": "<string>"
  }
}
```

| Field | Type | Source |
|---|---|---|
| `name` | string | Package manifest |
| `version` | string | Package manifest |
| `architecture` | string | Package manifest |
| `description` | string | Package manifest (OPTIONAL; empty string if absent) |
| `license` | string | Package manifest (OPTIONAL) |
| `homepage` | string | Package manifest (OPTIONAL) |
| `dependencies` | array | Package manifest (object schema per §4.1.1) |
| `optional_dependencies` | array | Package manifest |
| `conflicts` | array | Package manifest |
| `provides` | array | Package manifest |
| `replaces` | array | Package manifest |
| `side_effects` | array | Package manifest |
| `size_compressed` | integer | Size of the `.peipkg` file in bytes |
| `size_installed` | integer | Total installed size in bytes (mirror of manifest field) |
| `hash` | object | Hash of the `.peipkg` file (§3.5.2) |
| `url` | string | URL to fetch the package file (§6.4) |
| `build` | object | Subset of the manifest's build object: `timestamp` and `farm_id` only |

A package entry MUST contain `name`, `version`,
`architecture`, `dependencies`, `conflicts`,
`size_compressed`, `size_installed`, `hash`, and `url`.
Other fields are RECOMMENDED but MAY be omitted.

`size_compressed` and `size_installed` are required to
enable consumer-side enforcement of decompression bounds
(§3.5.4).

## Derivation rule

The active index is a derived view of the packages it
advertises. Every field in a package entry MUST exactly
match the corresponding field in the package's manifest
(§3.3) where one exists, and MUST exactly match the
properties of the actual `.peipkg` file (`hash`,
`size_compressed`, `url`).

If a package's manifest contradicts the index entry, the
manifest is authoritative (§3.3.7). Tooling that generates
the active index MUST extract values directly from package
manifests; manual editing of the index is forbidden.

## Field omissions

The active index intentionally omits the following manifest
fields:

- `sd_overrides`: not relevant to client-side resolution.
- `build.source_ref`: long, low-information-density;
  consult the package directly when needed.
- `schema_version` (manifest): redundant; the index has
  its own schema_version.

These fields remain in the package's manifest and are
available to consumers that fetch the package.

## URL field

The `url` field declares where the package file is
fetched from. The URL MAY be relative or absolute:

- A relative URL (starting with `/` or with no scheme) is
  resolved against the repository's `<repo-base>`.
- An absolute URL is used as-is.

The conventional form is a relative URL following the
structure defined in §6.4:

```
"url": "/p/nginx/1.26.2-3/nginx_1.26.2-3_x86_64.peipkg"
```

This form keeps the index portable: the same index file is
valid at any `<repo-base>` that hosts the same package
files.

## Hash object

```json
{
  "algorithm": "sha256",
  "value": "<lowercase hex>"
}
```

The `algorithm` MUST be `sha256` in this specification.
The `value` is the lowercase hexadecimal SHA-256 of the
`.peipkg` file in its compressed on-wire form.

## Ordering

The `packages` array MUST be sorted lexicographically by
`name`. Two entries with the same `name` within the active
index are INVALID. Each name appears exactly once.

> [!INFORMATIVE]
> Per-name uniqueness in the active index is what makes it
> "active": one current version of each package. The
> archive index (§6.3) relaxes this constraint to permit
> multiple versions per name.

## Forward-compatible fields

Consumers MUST ignore unknown fields in the index entry
(top-level or per-package) per the manifest forward-
compatibility rule (§3.3.3). Producers MAY emit
additional fields in future schema versions.

The exception is fields whose meaning is critical to
correctness (such as a hash algorithm field): these are
expected to be addressed via `schema_version` bumps, not
silent additions.

## Size

For a repository of approximately 300 packages, the active
index is on the order of 100 KB compressed and 600 KB
uncompressed. Consumers SHOULD fetch with HTTP-level
compression (`Accept-Encoding: zstd` or `gzip`) when
available.

> [!INFORMATIVE]
> The index is small enough for routine sync operations
> not to be a bandwidth concern at the v1 expected scale.
> If a future version of Peios reaches a scale where a
> single-file index becomes unwieldy (the practical limit
> is approximately 5,000 packages), the format may be
> extended with sharding mechanisms.

## Caching

Consumers SHOULD cache the parsed active index between
package manager invocations. The index changes only when
the producer publishes new content; re-parsing on every
operation is wasteful given that the change cadence is
much slower than the read cadence.

A cached parsed index remains valid until the consumer
performs a refresh operation (§6.5.4) that supersedes
it. The freshness policy is implementation-defined;
typical policies are time-based (TTL), explicit-refresh-
only, or check-on-network-state-change.

The cached index file MUST be stored under a security
descriptor that grants write access only to the package
manager principal. The package manager MUST re-verify
the cached index's signature on each install operation
rather than trusting the cache state across operations.
Caching avoids re-parsing JSON; it does not avoid
re-verifying signatures.

> [!INFORMATIVE]
> Without re-verification, an attacker who can write to
> the cache file (bypassing the SD) could substitute
> malicious metadata between cache write and install
> read. Re-verifying on every install closes that
> race; the cost is small (signature verification on a
> ~600 KB file is sub-millisecond).

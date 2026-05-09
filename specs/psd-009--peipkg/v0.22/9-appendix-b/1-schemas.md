---
title: JSON Schemas
---

> [!INFORMATIVE]
> This appendix consolidates all JSON schemas defined
> normatively elsewhere in the specification. The
> normative definitions are in the chapters cited in
> each section below; this appendix is a cross-reference,
> not a separate definition. Where this appendix and a
> normative chapter conflict, the normative chapter wins.

## Manifest

Defined normatively in §3.3.

```json
{
  "schema_version": 1,
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
  "size_installed": <integer>,
  "sd_overrides": [<sd_override>...],
  "build": {
    "timestamp": "<RFC 3339>",
    "farm_id": "<string>",
    "source_ref": "<string>"
  }
}
```

| Field | Required | Defining section |
|---|---|---|
| `schema_version` | yes | §3.3.2 |
| `name` | yes | §3.3.2, §2.1 |
| `version` | yes | §3.3.2, §2.2 |
| `architecture` | yes | §3.3.2, §2.3 |
| `description` | no | §3.3.3 |
| `license` | no | §3.3.3 |
| `homepage` | no | §3.3.3 |
| `dependencies` | yes (MAY be empty) | §3.3.2, §4.1 |
| `optional_dependencies` | no | §3.3.3, §4.1 |
| `conflicts` | yes (MAY be empty) | §3.3.2, §4.1.2 |
| `provides` | no | §3.3.3, §4.1.4 |
| `replaces` | no | §3.3.3, §4.1.5 |
| `side_effects` | no | §3.3.3, §4.3 |
| `size_installed` | yes | §3.3.2 |
| `sd_overrides` | no | §3.3.3, §3.3.5 |
| `build` | yes | §3.3.2, §3.3.4 |

## Dependency

Defined normatively in §4.1.1.

```json
{
  "name": "<string>",
  "constraint": "<string>",
  "arch": "<string>"
}
```

`name` required; `constraint` and `arch` optional. `arch`
defaults to `any`.

## Conflict

Defined normatively in §4.1.2. Schema identical to
dependency.

## Provides

Defined normatively in §4.1.4.

```json
{
  "name": "<string>",
  "version": "<string>"
}
```

`name` required; `version` optional.

## Replaces

Defined normatively in §4.1.5.

```json
{
  "name": "<string>",
  "constraint": "<string>"
}
```

`name` required; `constraint` optional.

## SD override

Defined normatively in §3.3.5.

```json
{
  "path": "<payload-relative path>",
  "sd": "<base64-encoded SD>"
}
```

Both fields required. Path MUST refer to a regular-file
or directory tar entry, never a symlink.

## Files manifest

Defined normatively in §3.5.1.

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "entries": [
    {
      "path": "<string>",
      "size": <integer>,
      "hash": "<lowercase hex>"
    }
  ]
}
```

Stored at `.peipkg/files.json`. Contains exactly one entry
per regular-file payload entry in the tar archive.

## Signature envelope

Defined normatively in §5.1.3.

```json
{
  "schema_version": 1,
  "algorithm": "ed25519",
  "key_fingerprint": "<lowercase hex SHA-256, 64 chars>",
  "signature": "<base64 without padding>"
}
```

Stored at `.peipkg/signature` as the last named tar entry.

Strict parsing: unknown fields cause rejection (deliberate
exception to the manifest's permissive forward-compat
rule).

## Repository descriptor

Defined normatively in §6.1.

```json
{
  "schema_version": 1,
  "repo": {
    "name": "<string>",
    "description": "<string>",
    "signing": {
      "algorithm": "ed25519",
      "keys": [
        {
          "fingerprint": "<lowercase hex>",
          "url": "<string>",
          "status": "active|transitioning"
        }
      ]
    }
  },
  "indexes": {
    "active": {
      "url": "<string>",
      "signature_url": "<string>"
    },
    "archive": {
      "url": "<string>",
      "signature_url": "<string>"
    }
  }
}
```

Each `keys` entry has the form:

```json
{
  "fingerprint": "<string>",
  "url": "<string>",
  "status": "active|transitioning|revoked",
  "valid_until": "<RFC 3339>"
}
```

`valid_until` is REQUIRED for `transitioning` keys and
ignored for other statuses.

Hosted at `<repo-base>/repo.json`. Detached signature at
`<repo-base>/repo.json.sig`.

## Active index

Defined normatively in §6.2.

```json
{
  "schema_version": 1,
  "repo": "<string>",
  "kind": "active",
  "index_version": <integer>,
  "generated_at": "<RFC 3339>",
  "packages": [<package_entry>...]
}
```

One entry per package; entries sorted lexicographically
by `name`; one version per `name`.

`index_version` is monotonically increasing across
publications; consumers enforce non-decreasing refresh
to defend against rollback attacks.

## Archive index

Defined normatively in §6.3.

Top-level schema identical to active index (§6.2.2)
except `kind` is `archive` and entries MAY repeat by
`name` (one entry per historical version).

Sorted lexicographically by `name`, then by `version`
descending within name.

## Index package entry

Defined normatively in §6.2.4.

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
    "algorithm": "sha256",
    "value": "<lowercase hex>"
  },
  "url": "<string>",
  "build": {
    "timestamp": "<RFC 3339>",
    "farm_id": "<string>"
  }
}
```

Required: `name`, `version`, `architecture`,
`dependencies`, `conflicts`, `size_compressed`,
`size_installed`, `hash`, `url`. Other fields recommended
but optional. `size_compressed` and `size_installed` are
required to enable consumer-side decompression-bounds
enforcement (§3.5.4).

The index package entry omits the manifest's
`sd_overrides` field, the `build.source_ref` field, and
the manifest's own `schema_version` field. These remain
in the package's own manifest.

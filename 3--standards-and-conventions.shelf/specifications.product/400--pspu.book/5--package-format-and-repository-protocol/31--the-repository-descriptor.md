---
title: The Repository Descriptor
description: The small JSON document at a well-known URL that is a repository's entry point — its schema, signing keys, index pointers and canonical form.
---

A repository descriptor is a small JSON document at a well-known URL
describing a repository's identity, its signing keys, and where its
indexes live. It is the entry point a consumer fetches when adding or
refreshing a repository.

## Location

A repository's descriptor MUST be reachable at `<repo-base>/repo.json`,
where `<repo-base>` is the base URL the repository was added under
(§5.36). It MUST be served as static content.

## Schema

```json
{
  "schema_version": 1,
  "repo": {
    "name": "<string>",
    "description": "<string>",
    "signing": { "algorithm": "<string>", "keys": [<key>...] }
  },
  "indexes": {
    "active":  { "url": "<string>", "signature_url": "<string>" },
    "archive": { "url": "<string>", "signature_url": "<string>" }
  }
}
```

| Field | Description |
|---|---|
| `schema_version` | MUST be 1 in this version. |
| `repo.name` | A short identifier for the repository. MUST be non-empty. SHOULD be kebab-case. |
| `repo.description` | OPTIONAL. A human-readable one-line description. |
| `repo.signing` | Signing key information. |
| `indexes.active` | Pointer to the active index (§5.33). |
| `indexes.archive` | Pointer to the archive index (§5.35). REQUIRED. |

The archive pointer is required even when the archive is empty, as it is
for a newly established repository. A repository without an archive
index is non-conformant.

## The signing object

```json
{
  "algorithm": "ed25519",
  "keys": [
    { "fingerprint": "<hex>", "url": "<string>", "status": "active" }
  ]
}
```

| Field | Description |
|---|---|
| `algorithm` | MUST be `ed25519` in this version. |
| `keys` | One or more keys. MUST contain at least one with status `active`. |

| Key field | Description |
|---|---|
| `fingerprint` | The key's fingerprint (§5.29): lowercase hex, 64 characters. |
| `url` | Where the public key file is published. MAY be relative to `<repo-base>`. |
| `status` | One of `active`, `transitioning`, `revoked` (§5.32). |
| `valid_until` | RFC 3339 UTC timestamp after which a `transitioning` key MUST NOT be accepted. REQUIRED for `transitioning`; ignored otherwise. |

The `keys` array MUST be sorted lexicographically by `fingerprint`. Two
entries with the same fingerprint in one descriptor are invalid.

## Index pointers

| Field | Description |
|---|---|
| `url` | Where the index is published. MAY be relative to `<repo-base>`. |
| `signature_url` | Where the index's detached signature is published. MAY be relative to `<repo-base>`. |

The conventional URLs are:

```
<repo-base>/index/active.json
<repo-base>/index/active.json.sig
<repo-base>/index/archive.json
<repo-base>/index/archive.json.sig
```

A repository MAY use other URLs by declaring them. The descriptor's URLs
are authoritative; the conventional paths are defaults for tooling that
has nothing else to go on.

## Descriptor signing

The descriptor MUST be accompanied by a detached signature published at
`<repo-base>/repo.json.sig`. The detached signature is a signature
envelope (§5.28) over the SHA-256 digest of the descriptor file's exact
bytes — the same construction as a package signature.

The signing key MUST be one of the keys listed in the descriptor's own
`repo.signing.keys`, with status `active` or `transitioning`.

> [!NOTE]
> The descriptor signature defends against an attacker who can serve
> content from `<repo-base>` substituting alternate signing keys.
> Without it, whoever can substitute the descriptor can substitute the
> keys, and from there re-sign the indexes and the packages. The
> chicken-and-egg at first add is broken by the operator supplying an
> expected fingerprint out of band (§5.37).

A repository configured to permit unsigned content MAY publish an
unsigned descriptor and unsigned indexes. This is a security weakening
opted into per repository, and a consumer MUST NOT treat the absence of
a signature as a fetch failure for such a repository.

## Canonical form

The descriptor SHOULD be canonically formatted so that signing is
reproducible: fields in the schema's order, key arrays sorted as
specified, no trailing whitespace, a single trailing newline.

## Naming

A consumer MAY refer to a repository by a local handle of its own
choosing. When it does, it MUST NOT require that handle to equal
`repo.name`, and MUST NOT compare an index's `repo` field against the
local handle. An index's `repo` field is compared against the
descriptor's `repo.name`.

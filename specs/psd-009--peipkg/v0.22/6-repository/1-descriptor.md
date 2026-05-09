---
title: Descriptor
---

A repository descriptor is a small JSON document at a
well-known URL that describes the repository's identity,
signing keys, and the locations of its indexes. It is the
entry point a consumer fetches when adding or refreshing a
repository.

## URL convention

A repository's descriptor MUST be reachable at the URL
`<repo-base>/repo.json`, where `<repo-base>` is the base
URL declared when the repository was added.

The descriptor MUST be served as static content.

## Schema

```json
{
  "schema_version": 1,
  "repo": {
    "name": "<string>",
    "description": "<string>",
    "signing": {
      "algorithm": "<string>",
      "keys": [<key>...]
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

| Field | Type | Description |
|---|---|---|
| `schema_version` | integer | MUST be 1 in this specification. |
| `repo.name` | string | A short identifier for the repository. MUST be non-empty. SHOULD use kebab-case. |
| `repo.description` | string | OPTIONAL. A human-readable one-line description. |
| `repo.signing` | object | Signing key information. See §6.1.3. |
| `indexes.active` | object | Pointer to the active index (§6.2). |
| `indexes.archive` | object | Pointer to the archive index (§6.3). REQUIRED in this version. |

The `archive` index pointer is required even if the
archive is empty (a newly-established repository). A
repository without an archive index is non-conformant.

## Signing object

```json
{
  "algorithm": "ed25519",
  "keys": [
    {
      "fingerprint": "<hex string>",
      "url": "<string>",
      "status": "active"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `algorithm` | string | Signature algorithm. MUST be `ed25519` in this specification. |
| `keys` | array | One or more keys. MUST contain at least one key with `status` `active`. |

Each key entry has the following schema:

| Field | Type | Description |
|---|---|---|
| `fingerprint` | string | The key's fingerprint per §5.2.3 (lowercase hex SHA-256, 64 chars). |
| `url` | string | URL where the public key file is published. MAY be relative to `<repo-base>`. |
| `status` | string | One of `active`, `transitioning`, or `revoked`. See §6.1.4. |
| `valid_until` | string | OPTIONAL. RFC 3339 UTC timestamp after which a `transitioning` key MUST NOT be accepted. REQUIRED for `transitioning` keys; ignored for `active` and `revoked`. |

A `keys` array MUST be sorted lexicographically by
`fingerprint`. Two entries with the same fingerprint
within the same descriptor are INVALID.

## Key statuses

A key's `status` describes its role in the repository's
current operation:

- `active`: the key is currently used to sign new packages
  and indexes. Consumers MUST accept signatures from
  active keys.
- `transitioning`: the key was previously active and
  remains acceptable for verification until its
  `valid_until` timestamp, but is no longer used to
  produce new signatures. Consumers MUST accept
  signatures from transitioning keys when the current
  time is at or before `valid_until`. Consumers MUST
  reject signatures from transitioning keys whose
  `valid_until` has passed. See §5.2.6 for the rotation
  flow.
- `revoked`: the key is no longer trusted under any
  circumstance. Consumers MUST reject signatures from
  revoked keys regardless of when they were produced or
  whether they verify cryptographically. The `revoked`
  status is the explicit signal of a compromise event
  (§5.2.7); transitioning is for routine rotation only.

A repository MAY have multiple `active` keys (allowing
parallel signing), any number of `transitioning` keys
each with its own `valid_until`, and any number of
`revoked` keys.

A `transitioning` key entry MUST include a `valid_until`
timestamp.

A key whose status is something other than `active`,
`transitioning`, or `revoked` is INVALID.

A revoked entry MUST be retained in the descriptor for
at least one year after the revocation event. Premature
removal of a revoked entry would mask the public
acknowledgement of compromise from consumers with
stale caches.

> [!INFORMATIVE]
> The presence of a `revoked` key in a descriptor is
> useful even though revoked-key signatures are rejected
> regardless: it serves as a public acknowledgement of
> compromise that consumers can audit. The mandatory
> retention period ensures that consumers encountering
> signatures from the revoked key receive a clear
> "this key was revoked" signal rather than a generic
> "key not in trust set" error.

## Index pointers

Each index pointer object has the following schema:

| Field | Type | Description |
|---|---|---|
| `url` | string | URL where the index is published. MAY be relative to `<repo-base>`. |
| `signature_url` | string | URL where the index's detached signature is published. MAY be relative to `<repo-base>`. |

The conventional URLs are:

```
<repo-base>/index/active.json
<repo-base>/index/active.json.sig
<repo-base>/index/archive.json
<repo-base>/index/archive.json.sig
```

A repository MAY use other URLs by specifying them
explicitly. The descriptor's URLs are authoritative; the
conventional paths are fallbacks for tools that need a
sensible default.

## Descriptor signing

The descriptor itself MUST be accompanied by a detached
signature published at `<repo-base>/repo.json.sig`. The
signature is over the descriptor file's exact bytes,
encoded as Ed25519 base64 (RFC 4648 §4) without padding.

The signing key MUST be one of the keys listed in the
descriptor's `repo.signing.keys` array (any key with
status `active` or `transitioning`).

> [!INFORMATIVE]
> The descriptor signature defends against an attacker who
> can serve content from `<repo-base>` substituting
> alternate signing keys. Without descriptor signing, an
> attacker who can substitute the descriptor can substitute
> the signing keys, and from there can re-sign indexes and
> packages. The chicken-and-egg problem at initial repo
> add is broken by the user supplying an expected key
> fingerprint out-of-band (§6.5).

A repository configured to permit unsigned packages
(§6.5.3) MAY publish an unsigned descriptor and indexes.
This is a security weakening explicitly opted into per-
repository.

## Determinism

The descriptor JSON SHOULD be canonically formatted to
permit reproducible signing: keys ordered as specified in
the schema, key arrays sorted as specified, no trailing
whitespace, single trailing newline.

## Example

```json
{
  "schema_version": 1,
  "repo": {
    "name": "peios-official",
    "description": "Official Peios package repository",
    "signing": {
      "algorithm": "ed25519",
      "keys": [
        {
          "fingerprint": "1a2b3c...64chars",
          "url": "/keys/1a2b3c.pub",
          "status": "active"
        }
      ]
    }
  },
  "indexes": {
    "active": {
      "url": "/index/active.json",
      "signature_url": "/index/active.json.sig"
    },
    "archive": {
      "url": "/index/archive.json",
      "signature_url": "/index/archive.json.sig"
    }
  }
}
```

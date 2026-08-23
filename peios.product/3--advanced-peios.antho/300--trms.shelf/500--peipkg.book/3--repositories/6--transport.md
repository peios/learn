---
title: Transport
description: Everything a repository serves is a static file over HTTP — the size caps, URL resolution, supported schemes and failure handling.
---

Everything a repository serves is a static file fetched over HTTP.

## Size caps

Every fetch is capped, so that a hostile or broken server cannot exhaust
memory before anything has been verified.

| Artifact | Cap |
|---|---|
| Repository descriptor | 4 MiB |
| Detached signature | 4 KiB |
| Public key file | 64 KiB |
| Index | 64 MiB |
| Package file | the index-declared compressed size, plus an allowance |

The package allowance is a flat 16 MiB above the declared compressed
size, applied uniformly regardless of how large the package is.

## URL resolution

A URL in a descriptor or an index may be absolute, rooted, or
document-relative, and each resolves as PSPU §5.36 describes: an
absolute URL as-is, a leading-slash URL against the repository base, and
anything else against the document that carried it.

## Schemes

HTTPS is required unless the repository's insecure-transport setting is
enabled, and enabling it produces no warning of its own on subsequent
operations.

`file://` is supported for development and is exempt from the transport
check entirely rather than gated by the insecure-transport setting.

## Failure

A fetch failure is reported and fails the operation. peipkg does not
substitute cached data for a failed fetch without the operator saying
so.

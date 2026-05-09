---
title: URL Conventions
---

This section defines the URL structure repositories use to
serve their content. The conventions are designed for
static HTTP hosting: every URL maps to a static file or a
static-file-equivalent resource.

## Repository base

A repository is identified by a base URL, referred to as
`<repo-base>` throughout this specification.

The base URL MUST be a syntactically valid HTTP or HTTPS
URL per RFC 3986. HTTPS MUST be used unless the consumer
is configured with an explicit `allow_insecure_transport`
flag for the repository in question. The flag is per-
repository, not global, and its use MUST generate a
per-operation warning. HTTP repositories are intended
only for trusted local-network development scenarios;
relying on package signing alone for transport integrity
exposes the consumer to traffic-analysis and
metadata-substitution attacks even when content
verification succeeds.

Toggling `allow_insecure_transport` to true after the
repository has been added MUST require explicit operator
authorisation (§7.6.6) AND MUST emit an audit event to
eventd (§7.6.3). Setting the flag during the initial
repo-add operation is treated as part of the operator's
trust decision and does not require a separate audit
event beyond the standard repo-add audit.

The base URL MUST NOT have a trailing slash. The well-known
relative paths defined below are appended directly.

> [!INFORMATIVE]
> Examples:
>
> - `https://pkgs.peios.org`
> - `https://internal.example.com/peios`
> - `http://localhost:8000`
>
> A repository hosted under a path prefix (the second
> example) is permitted; relative URLs in indexes are
> resolved relative to this base.

## Conventional paths

The following paths are conventional. A repository SHOULD
use these paths unless it has a compelling reason to use
others. When a repository uses non-conventional paths, the
descriptor's URL fields (§6.1) declare them.

| Path | Content |
|---|---|
| `<repo-base>/repo.json` | Repository descriptor (§6.1) |
| `<repo-base>/repo.json.sig` | Detached signature on the descriptor |
| `<repo-base>/index/active.json` | Active index (§6.2) |
| `<repo-base>/index/active.json.sig` | Detached signature on the active index |
| `<repo-base>/index/archive.json` | Archive index (§6.3) |
| `<repo-base>/index/archive.json.sig` | Detached signature on the archive index |
| `<repo-base>/keys/<fingerprint>.pub` | Public key file, named by full fingerprint |
| `<repo-base>/p/<name>/<version>/<filename>` | Package file (§6.4.3) |

A consumer that knows only `<repo-base>` MUST be able to
locate `repo.json` at the conventional path. The descriptor
contains the URLs for everything else.

## Package URLs

Each package's URL has the form:

```
<repo-base>/p/<name>/<version>/<filename>
```

Where:

- `<name>` is the package name conforming to §2.1.
- `<version>` is the full version string conforming to
  §2.2.
- `<filename>` is `<name>_<version>_<architecture>.peipkg`
  per §2.1.4.

> [!INFORMATIVE]
> Example URL:
>
> ```
> https://pkgs.peios.org/p/nginx/1.26.2-3/nginx_1.26.2-3_x86_64.peipkg
> ```

## Sibling artifacts

The directory containing each package file MAY hold
additional sibling files for that package version. These
are not normative in this specification but are reserved
for future use:

```
<repo-base>/p/<name>/<version>/<filename>.debug.peipkg
<repo-base>/p/<name>/<version>/<filename>.sbom.json
<repo-base>/p/<name>/<version>/<filename>.attestation.json
```

A consumer of v0.22 MUST NOT attempt to fetch sibling
artifacts. A producer MAY publish them; their meaning is
defined by future versions of this specification.

## Public key URLs

Public key files referenced by the descriptor's signing
keys (§6.1.3) MAY be published anywhere reachable by URL.
The conventional path (`<repo-base>/keys/<fingerprint>.pub`)
co-locates them with the descriptor for static-host
simplicity.

A public key file MUST contain only the public key in one
of the encodings defined in §5.2.2.

## Relative URLs in indexes

URL fields in the descriptor and in indexes (§6.2 and §6.3)
MAY be absolute or relative.

- An absolute URL (with scheme) is used as-is.
- A URL beginning with `/` is resolved against
  `<repo-base>` by prepending the base.
- A URL with no scheme and no leading `/` is resolved
  against the URL of the document containing the
  reference per RFC 3986 §5.

> [!INFORMATIVE]
> Relative URLs are RECOMMENDED. They keep the index file
> portable: the same index is valid under any
> `<repo-base>` that hosts the same package layout.
> Absolute URLs in an index pin it to a specific host and
> require regeneration if the host changes.

## Static hosting requirements

The protocol requires only static HTTP serving. A
conformant repository MAY be hosted on:

- A simple HTTP server (nginx, Apache, Caddy)
- An object store with HTTP frontend (S3, R2, GCS)
- A static site host (GitHub Pages, Cloudflare Pages,
  Netlify)
- A CDN proxying any of the above
- A local filesystem accessed via `file://` URLs (for
  development)
- A combination (descriptor and indexes on a static host,
  package binaries on object storage with redirects)

There is no requirement for server-side computation,
dynamic responses, or content negotiation beyond
optional HTTP-level compression.

## Network failure handling

A consumer that fails to fetch a URL MUST NOT silently
fall back to outdated cached data without explicit user
authorisation. Stale cache use without explicit consent is
a security risk: it can mask substituted-content or
revoked-key updates.

A consumer SHOULD provide a mechanism for users to
configure cache-staleness tolerance per repository.

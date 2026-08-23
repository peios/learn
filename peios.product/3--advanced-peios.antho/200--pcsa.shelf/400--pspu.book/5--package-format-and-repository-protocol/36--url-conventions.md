---
title: URL Conventions
description: Every URL maps to a static file — the repository base, the conventional paths, sibling artifacts, hosting and network failure.
---

Every URL in this chapter maps to a static file. The protocol requires
no server-side computation, no dynamic response, and no content
negotiation beyond optional HTTP-level compression.

## The repository base

A repository is identified by a base URL, `<repo-base>`.

The base URL MUST be a syntactically valid HTTP or HTTPS URL per
RFC 3986, and MUST NOT have a trailing slash: the well-known relative
paths below are appended directly.

HTTPS MUST be used, unless the consumer has been configured with an
explicit **per-repository** insecure-transport allowance. There is no
global form of that allowance, and its use MUST generate a per-operation
warning.

Enabling the allowance on a repository that has already been added MUST
require explicit operator authorisation and MUST emit an audit event.
Setting it as part of the initial add is covered by the operator's trust
decision at that moment and requires no separate event beyond the add's
own.

> [!NOTE]
> Insecure transport is intended for a trusted local network during
> development. Relying on package signing alone for transport integrity
> leaves the consumer exposed to traffic analysis and to
> metadata-substitution attacks even when content verification succeeds.

A consumer MAY additionally support a `file://` base URL for local
development. A `file://` repository MUST be subject to the same
per-repository allowance as an HTTP one: it is not HTTPS, and admitting
it silently makes removable or network-mounted media a trusted source
without the operator ever acknowledging it.

## Conventional paths

| Path | Content |
|---|---|
| `<repo-base>/repo.json` | Repository descriptor (§5.31) |
| `<repo-base>/repo.json.sig` | Detached signature on the descriptor |
| `<repo-base>/index/active.json` | Active index (§5.33) |
| `<repo-base>/index/active.json.sig` | Detached signature on the active index |
| `<repo-base>/index/archive.json` | Archive index (§5.35) |
| `<repo-base>/index/archive.json.sig` | Detached signature on the archive index |
| `<repo-base>/keys/<fingerprint>.pub` | Public key file, named by full fingerprint |
| `<repo-base>/p/<name>/<version>/<filename>` | Package file |

A repository SHOULD use these paths unless it has a reason not to; when
it does not, the descriptor declares the ones it uses. A consumer that
knows only `<repo-base>` MUST be able to locate `repo.json` at the
conventional path. The descriptor carries the URLs for everything else.

## Package URLs

```
<repo-base>/p/<name>/<version>/<filename>
```

where `<name>` conforms to §5.3, `<version>` is the full version string
of §5.5, and `<filename>` is `<name>_<version>_<architecture>.peipkg`.

```
https://pkgs.peios.org/p/nginx/1.26.2-3/nginx_1.26.2-3_x86_64.peipkg
```

## Sibling artifacts

The directory containing a package file MAY hold additional siblings for
that version. These are reserved for future use and are not normative
here:

```
<repo-base>/p/<name>/<version>/<filename>.debug.peipkg
<repo-base>/p/<name>/<version>/<filename>.sbom.json
<repo-base>/p/<name>/<version>/<filename>.attestation.json
```

A consumer conforming to this version MUST NOT attempt to fetch a
sibling artifact. A producer MAY publish them; their meaning is defined
by a future version.

## Relative URLs

A URL field in a descriptor or an index MAY be absolute or relative.

- An absolute URL, carrying a scheme, is used as-is.
- A URL beginning with `/` is resolved against `<repo-base>` by
  prepending the base.
- A URL with neither a scheme nor a leading `/` is resolved against the
  URL of the document containing the reference, per RFC 3986 §5.

> [!NOTE]
> Relative URLs are RECOMMENDED: they keep an index portable, valid
> under any `<repo-base>` hosting the same layout. An absolute URL pins
> the index to a host and requires regeneration when the host changes.

## Hosting

A conformant repository may be hosted on a plain HTTP server, an object
store with an HTTP frontend, a static site host, a CDN in front of any
of those, or a combination — descriptor and indexes on a static host,
package files on object storage behind redirects.

## Network failure

A consumer that fails to fetch a URL MUST NOT silently fall back to
outdated cached data. Using a stale cache without explicit operator
consent can mask substituted content or a revoked-key update.

A consumer SHOULD offer a way to configure cache-staleness tolerance per
repository.

A consumer whose cached index for a configured repository fails to load
or verify MUST treat that as a failure of the operation rather than
proceeding without that repository.

> [!NOTE]
> Silently continuing is worse than it looks. Dropping a repository from
> consideration mid-operation does not merely lose candidates: it can
> silently promote a lower-priority repository's package into a role the
> dropped one was filling, which is an escalation dressed as a warning.

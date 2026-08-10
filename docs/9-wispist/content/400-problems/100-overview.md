---
title: Problem Details
type: reference
description: Wispist errors use RFC 9457 Problem Details with permanent type URIs, request-correlated instances, stable titles, and ergonomic browser codes.
related:
  - wispist/reference/http-api
  - wispist/reference/browser-api
  - wispist/problems/revision-conflict
  - wispist/problems/rate-limited
---

Wispist API errors use RFC 9457 Problem Details and `application/problem+json`:

```json
{
  "type": "https://learn.peios.org/wispist/problems/revision-conflict/",
  "title": "Revision conflict",
  "status": 412,
  "detail": "The document changed after it was read.",
  "instance": "urn:uuid:019c0000-0000-7000-8000-000000000000"
}
```

The type URI is the primary machine identifier. It is permanent even if the implementation or documentation later moves. `title` is stable for that type; `detail` describes this occurrence. `status` matches the HTTP status.

`instance` is a `urn:uuid:` URI built from the same UUID returned in `X-Request-ID`. Give that request ID to an operator when investigating a server-side failure.

Validation problems may add an `errors` array of JSON Pointer and detail objects. Internal SQL, paths, stack traces, document bodies, tokens, and policy predicates are never returned.

The browser client maps known type URIs to convenient `error.code` values:

| HTTP | Type | Browser code |
| ---: | --- | --- |
| 400 | [Invalid request](~wispist/problems/invalid-request) | `invalid_request` |
| 400 | [Invalid JSON](~wispist/problems/invalid-json) | `invalid_json` |
| 401 | [Authentication required](~wispist/problems/authentication-required) | `authentication_required` |
| 403 | [Forbidden](~wispist/problems/forbidden) | `forbidden` |
| 404 | [Not found](~wispist/problems/not-found) | `not_found` |
| 405 | [Method not allowed](~wispist/problems/method-not-allowed) | `method_not_allowed` |
| 409 | [Idempotency conflict](~wispist/problems/idempotency-conflict) | `idempotency_conflict` |
| 409 | [Quota exceeded](~wispist/problems/quota-exceeded) | `quota_exceeded` |
| 412 | [Revision conflict](~wispist/problems/revision-conflict) | `revision_conflict` |
| 413 | [Request too large](~wispist/problems/request-too-large) | `request_too_large` |
| 415 | [Unsupported media type](~wispist/problems/unsupported-media-type) | `unsupported_media_type` |
| 428 | [Precondition required](~wispist/problems/precondition-required) | `precondition_required` |
| 429 | [Rate limited](~wispist/problems/rate-limited) | `rate_limited` |
| 503 | [Temporarily unavailable](~wispist/problems/temporarily-unavailable) | `temporarily_unavailable` |

HTTP headers retain their normal authority. `Retry-After`, `ETag`, `Allow`, and `WWW-Authenticate` are not replaced by Problem Details members.

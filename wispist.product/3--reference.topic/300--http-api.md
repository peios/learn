---
title: HTTP API reference
type: reference
description: Wispist v1 routes, JSON envelopes, conditional requests, idempotency, pagination, change streams, headers, and same-origin requirements.
related:
  - wispist/reference/browser-api
  - wispist/reference/wispist-json
  - wispist/problems/overview
  - wispist/using-wispist/live-updates
---

Wispist v1 is served from the hosted site's own origin under `/_wispist/`:

```text
GET    /_wispist/client/v1.js
GET    /_wispist/v1
GET    /_wispist/v1/collections/{collection}/documents
POST   /_wispist/v1/collections/{collection}/documents
GET    /_wispist/v1/collections/{collection}/documents/{document}
PUT    /_wispist/v1/collections/{collection}/documents/{document}
DELETE /_wispist/v1/collections/{collection}/documents/{document}
GET    /_wispist/v1/changes
```

Use the browser client unless direct HTTP control is necessary.

## General rules

- API responses use `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.
- JSON responses use `application/json; charset=utf-8`.
- JSON request bodies require `Content-Type: application/json`.
- Every response includes `X-Request-ID`. A caller-provided UUID may be retained.
- Errors use RFC 9457 `application/problem+json`.
- Unsupported methods on known resources return `405` with `Allow`.
- Paths and identifiers must be decoded, canonical, and free of encoded separators or dot segments.
- No CORS permission is emitted.

Unsafe requests require one exact same-origin `Origin` header. If `Sec-Fetch-Site` is present, it must be `same-origin`.

## Service description

```http
GET /_wispist/v1
```

```json
{
  "name": "Wispist",
  "version": 1,
  "mode": "live",
  "readOnly": false,
  "collections": ["before-you-go"]
}
```

## List documents

```http
GET /_wispist/v1/collections/before-you-go/documents?limit=100&after=opaque
```

`limit` defaults to 100 and may be 1 to 250. `after` is an opaque pagination cursor.

```json
{
  "documents": [
    {
      "id": "passport",
      "revision": "opaque",
      "createdAt": "2026-07-13T12:34:56.123Z",
      "updatedAt": "2026-07-13T12:34:56.123Z",
      "data": { "text": "Pack passport", "done": false }
    }
  ],
  "after": null,
  "changes": "opaque-change-cursor"
}
```

The `changes` cursor is captured by the first page and repeated by later pages. List all pages, then consume changes after it to reconcile concurrent mutations.

## Create a generated ID

```http
POST /_wispist/v1/collections/before-you-go/documents
Origin: https://site.example
Idempotency-Key: a-strong-random-value
Content-Type: application/json

{"data":{"text":"Buy insurance","done":false}}
```

The key is required and contains 16 to 128 visible ASCII characters. The same namespace, key, and request fingerprint returns the original `201 Created` response for at least 24 hours. Reusing the key for a different request returns [idempotency conflict](~wispist/problems/idempotency-conflict).

The response includes `Location`, the document ETag, and the complete envelope.

## Read

```http
GET /_wispist/v1/collections/before-you-go/documents/passport
```

The ETag is the quoted opaque revision. `If-None-Match` supports wildcard, lists, and weak comparison for GET/HEAD and may return `304 Not Modified`.

## Create or replace a selected ID

Create only:

```http
PUT /_wispist/v1/collections/before-you-go/documents/passport
Origin: https://site.example
If-None-Match: *
Content-Type: application/json

{"data":{"text":"Pack passport","done":false}}
```

Replace:

```http
PUT /_wispist/v1/collections/before-you-go/documents/passport
Origin: https://site.example
If-Match: "observed-revision"
Content-Type: application/json

{"data":{"text":"Pack passport","done":true}}
```

Exactly one precondition is required. Create returns `201`; replacement returns `200`. Both return a new document and ETag.

## Delete

```http
DELETE /_wispist/v1/collections/before-you-go/documents/passport
Origin: https://site.example
If-Match: "observed-revision"
```

Success is `204 No Content`. The deletion appends a change containing ID and deleted revision but no document body.

## Change stream

```http
GET /_wispist/v1/changes?collections=before-you-go&after=opaque
Accept: text/event-stream
```

`collections` is repeatable with 1 to 8 distinct declared values. Every collection must permit `subscribe` and `read`.

```text
id: opaque-change-cursor
event: change
data: {"collection":"before-you-go","operation":"update","document":{...}}

```

A deletion supplies `id` and `revision` instead of `document`. A `reset` event means the client must list again. If `after` is absent, the stream begins after the current high-water mark and does not replay the collection.

The server sends heartbeat comments while otherwise idle. Delivery is at least once; de-duplicate by cursor.

## See also

- [Browser API reference](~wispist/reference/browser-api) — the supported client over these routes.
- [Problem Details](~wispist/problems/overview) — the error shape every route uses.
- [Limits and abuse controls](~wispist/reference/limits) — body, pagination, stream, and rate bounds.

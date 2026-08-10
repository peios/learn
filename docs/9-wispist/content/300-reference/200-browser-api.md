---
title: Browser API reference
type: reference
description: Complete reference for the automatic global Wispist client, collection CRUD methods, subscriptions, environment fields, and WispistError.
related:
  - wispist/reference/wispist-json
  - wispist/reference/http-api
  - wispist/using-wispist/live-updates
  - wispist/problems/overview
---

Wispdeck defines one non-enumerable, non-writable global before site-authored elements run:

```text
wispist.version
wispist.mode
wispist.readOnly
wispist.collection(name)
```

There is no connect method. The client makes no request during evaluation.

## Environment fields

| Field | Type | Meaning |
| --- | --- | --- |
| `version` | number | Client protocol major; `1`. |
| `mode` | string | `live`, `draft`, or `live-preview`. |
| `readOnly` | boolean | Whether the host has forced mutations off. |

`mode` and `readOnly` are synchronous presentation metadata. The server enforces the real binding independently.

## Collection handle

```js
const items = wispist.collection("before-you-go");
```

`collection(name)` validates the collection-name grammar locally and returns a frozen handle. The server still requires the active release to declare it.

### `list(options?)`

Returns a promise for every document in creation order. `options.limit` selects the page size from 1 to 250; the client follows pagination automatically.

```js
const documents = await items.list({ limit: 100 });
```

### `get(id)`

Returns one complete document envelope or rejects with `not_found`.

```js
const document = await items.get("passport");
```

### `add(data)`

Creates a generated-ID document and returns it. `data` must be a non-null object and not an array. The client generates the required idempotency key.

```js
const document = await items.add({ text: "Passport", done: false });
```

### `create(id, data)`

Creates exactly the selected ID and returns it. It uses create-only semantics and rejects with `revision_conflict` if that ID exists.

### `replace(document, data)`

Conditionally replaces the observed document with `data` and returns the new envelope. A concurrent change rejects with `revision_conflict`.

### `update(document, changes)`

Shallow-merges `changes` into `document.data` locally, then performs `replace`.

```js
const updated = await items.update(document, { done: true });
```

An `undefined` change is omitted by JSON serialization but does not delete the old property from the local merge. To remove properties or make nested changes, construct the complete new object and call `replace`.

### `delete(document)`

Conditionally deletes the observed document. The promise resolves with no value.

## Subscribe

```js
const unsubscribe = items.subscribe((documents, event) => {
  render(documents);
}, {
  limit: 250,
  onError(error) {
    showError(error);
  },
});
```

The callback runs once with `event.type === "initial"` and after each applied change. Documents remain in creation order, with ID as the deterministic tie-breaker.

The client reconnects recoverable EventSource failures with bounded exponential backoff and jitter. A server `reset` causes a fresh list. `onError` receives initial or terminal errors; ordinary reconnects do not create unhandled promise rejections.

`subscribe` returns the unsubscribe function immediately.

## `WispistError`

Rejected operations use an Error subclass with:

| Field | Meaning |
| --- | --- |
| `name` | Always `WispistError`. |
| `type` | RFC 9457 problem type URI, when an HTTP problem was returned. |
| `code` | Ergonomic code mapped from a known problem type. |
| `title` | Stable problem title. |
| `detail` | Safe occurrence-specific explanation. |
| `status` | HTTP status, when available. |
| `instance` | Problem occurrence URI, when available. |
| `requestId` | `X-Request-ID` value, when available. |
| `problem` | Complete decoded Problem Details object. |

The wire protocol does not contain a separate code. `type` is the stable machine identifier; `code` is client convenience. Network failures use `network_error` without a type or HTTP status. An invalid non-problem response uses `invalid_response`.

Known codes are listed in [Problem Details](~wispist/problems/overview).

## Browser dependencies and side effects

The client uses `fetch`, `EventSource`, and Web Crypto. It has no package dependency, local-storage use, service worker, analytics, or telemetry. Requests are same-origin, use same-origin credentials, and disable browser caching.

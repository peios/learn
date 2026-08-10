---
title: Live updates
type: concept
description: How Wispist subscriptions combine paginated snapshots, retained changes, Server-Sent Events, reconnection, and reset without polling.
related:
  - wispist/reference/browser-api
  - wispist/reference/http-api
  - wispist/reference/limits
  - wispist/problems/rate-limited
---

`collection.subscribe(callback)` keeps one collection view current without polling. It combines an initial paginated list with a same-origin Server-Sent Events stream.

## Snapshot, then changes

Opening a subscription does four things:

1. Lists every page of the collection.
2. Records the change cursor captured at the first page.
3. Opens `/_wispist/v1/changes` after that cursor.
4. Applies create, update, and delete events to an in-memory map.

Pagination is not a frozen SQLite snapshot across requests. The cursor is what closes the gap: mutations that race the list appear in the retained change stream after the first page's watermark.

The callback receives the complete ordered document array and an event:

```js
const stop = checklist.subscribe((documents, event) => {
  render(documents);
  if (event.type === "initial") {
    console.log("Initial state is ready");
  }
}, {
  onError(error) {
    showStatus(error.detail);
  },
});
```

Call `stop()` to close the stream and cancel reconnect work.

## Delivery and reconnection

Wispist commits a mutation before publishing it to in-memory listeners. On connection, the server registers the listener before reading retained changes, sends the backlog, removes duplicate queued events by cursor, and then continues live.

Delivery is at least once. Cursors are opaque and the client de-duplicates them. Ordinary disconnects reconnect with bounded exponential backoff and jitter.

Change history is finite. If a cursor is older than retained history, or a subscriber falls behind its bounded event queue, the server sends a `reset` event and closes. The browser client relists automatically rather than risking silent divergence.

## Active compute only

An open EventSource is active work. Wispist caps streams per site and client address and sends periodic comments to keep healthy intermediaries from treating an idle connection as abandoned.

There is no listener, poller, or goroutine for a site with no active subscription. Reading an untouched collection or opening its first stream does not create a SQLite file; the first mutation does.

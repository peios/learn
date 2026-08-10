---
title: Documents and collections
type: concept
description: Understand Wispist namespaces, declared collections, document envelopes, revisions, ordering, and conditional mutation semantics.
related:
  - wispist/reference/wispist-json
  - wispist/reference/browser-api
  - wispist/problems/revision-conflict
  - wispist/using-wispist/drafts-and-publishing
---

Wispist stores JSON objects as revisioned documents inside declared collections. The host supplies the namespace; site code selects only a collection and, where needed, a document ID.

## Namespaces are the isolation boundary

A namespace is opaque to Wispist. It cannot be selected through the browser API and is never inferred from a collection name. Wispdeck binds every request to a stable site store and either its `live` or `draft` namespace.

The same collection name in two sites, or in one site's live and draft views, addresses different data. Republishing does not change the site's stable store key.

## Collections must be declared

A collection exists for browser access only when the active release declares it in `wispist.json`. Removing the declaration hides stored documents but does not delete them. Re-adding it makes them accessible again.

Names are 1 to 48 ASCII bytes, begin with a lowercase letter, and continue with lowercase letters, digits, hyphens, or underscores:

```text
[a-z][a-z0-9_-]{0,47}
```

Collection order is document creation order, with ID as the deterministic tie-breaker.

## A document has server and caller fields

```json
{
  "id": "passport",
  "revision": "opaque-revision-token",
  "createdAt": "2026-07-13T12:34:56.123Z",
  "updatedAt": "2026-07-13T12:35:04.456Z",
  "data": {
    "text": "Pack passport",
    "done": false
  }
}
```

Wispist owns `id`, `revision`, `createdAt`, and `updatedAt`. The caller owns `data`, whose root must be a JSON object. Nested arrays, objects, strings, numbers, booleans, and `null` are allowed.

JSON is strict. Invalid UTF-8, duplicate member names, more than 32 nesting levels, keys longer than 256 UTF-8 bytes, and oversized representations are rejected. Wispist stores compact JSON but does not give object-member order any meaning.

IDs may be caller-selected or generated. They contain 1 to 64 ASCII letters, digits, underscores, or hyphens and are case-sensitive. `.` and `..` are not valid IDs.

## Revisions prevent silent overwrite

A revision identifies one incarnation of one document. Every successful create or replacement produces a new opaque value, and deleting then recreating an ID does not reuse an old revision.

The easiest safe operations are the browser client's document-envelope methods:

```js
const observed = await checklist.get("passport");
const changed = await checklist.update(observed, { done: true });
await checklist.delete(changed);
```

`update` and `delete` carry the observed revision. If another caller changed the document first, Wispist returns `revision_conflict`. It never falls back to last-write-wins.

Creating a deterministic ID uses create-only semantics:

```js
await checklist.create("passport", {
  text: "Pack passport",
  done: false,
});
```

That operation fails with a revision conflict if `passport` already exists.

## One document per transaction

Each create, replacement, or deletion commits the document state and one ordered change record in the same SQLite transaction. A subscriber can therefore never observe a change whose document mutation failed to commit.

V1 does not provide multi-document transactions. Model one atomic unit as one document when several fields must change together.

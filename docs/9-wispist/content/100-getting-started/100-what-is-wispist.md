---
title: What Wispist is
type: concept
description: Wispist gives simple browser sites persistent JSON documents and live updates without a connection step, browser-visible secret, or dedicated application server.
related:
  - wispist/getting-started/build-a-shared-checklist
  - wispist/using-wispist/documents-and-collections
  - wispist/reference/wispist-json
  - wispist/reference/browser-api
---

**Wispist** is a lightweight data engine for simple websites. It gives ordinary HTML and JavaScript a persistent document store, safe concurrent mutations, and live updates while keeping the site itself static.

On a Wispdeck-hosted site, Wispist is already there:

```js
const checklist = wispist.collection("before-you-go");

const item = await checklist.add({
  text: "Buy travel insurance",
  done: false,
});

await checklist.update(item, { done: true });
```

There is no connection call, project identifier, endpoint, API key, or secret in that code. Wispdeck identifies the site and its active release from the request, then supplies an opaque namespace and policy to the embedded Wispist Engine. The same-origin browser client cannot choose another site's store.

## Static code, persistent data

A Wispist site is still a static bundle:

```text
site.zip
├── index.html
├── app.js
├── styles.css
└── wispist.json
```

`wispist.json` declares which collections the release may use and who may perform each operation. Wispdeck validates that declaration when the bundle is uploaded. It inserts a small parser-blocking client before site-authored elements in every served HTML `head`, making `globalThis.wispist` available before later site scripts run.

The site's documents live in SQLite, outside the immutable release. Republishing code therefore keeps production data. An idle site has no dedicated process, timer, poller, goroutine, or database connection; work happens only while a viewer or mutation is active.

## The data model

Wispist v1 has three main concepts:

- A **namespace** is the host-selected isolation boundary. Wispdeck uses separate `live` and `draft` namespaces for each site.
- A **collection** is a declared, ordered set of documents, such as `before-you-go`.
- A **document** contains an opaque ID, an opaque revision, server timestamps, and a caller-owned JSON object in `data`.

Every replacement and deletion is conditional on an observed revision. If two browsers edit the same document concurrently, one succeeds and the other receives a [revision conflict](~wispist/problems/revision-conflict) rather than silently overwriting work it did not see.

Subscriptions use Server-Sent Events. The client first lists a consistent collection view, then consumes retained changes after that list cursor. It reconnects after ordinary network interruptions and relists if the retained history is no longer sufficient.

## Policy is public, enforcement is not

The release declaration contains policy, not credentials. The concise `shared` profile deliberately allows every visitor to list, read, create, update, delete, and subscribe:

```json
{
  "version": 1,
  "collections": {
    "before-you-go": {
      "access": "shared"
    }
  }
}
```

That is suitable for a genuinely public collaborative checklist. It is not user authorization. Exact-origin checks, quotas, and request limits reduce cross-site and automated abuse, but any visitor can still change a `shared` collection.

Expanded declarations can set every operation to `anyone`, `authenticated`, or `nobody`. Wispdeck's first integration supplies anonymous principals to hosted site code, so `authenticated` is reserved for future identity integration rather than a way to reuse the dashboard cookie.

## Draft and live state

Wispdeck previews use a fresh private origin. Draft code reads and writes the site's draft namespace. The Current selector on that preview origin reads the live namespace with an unconditional server-side read-only override.

Publishing changes which release supplies public code and policy. It does not promote draft documents, clear live documents, or create a new production store. This prevents test data from silently replacing real data.

## What v1 deliberately leaves out

Wispist v1 is document CRUD plus live collection updates. It does not expose SQL, run user functions, execute scheduled jobs, perform joins, provide offline conflict resolution, accept file uploads, or offer multi-document transactions. It supports one active process for a data directory.

The small surface is intentional: Wispist is for the state that turns a static page into a useful little shared application, not a general application server.

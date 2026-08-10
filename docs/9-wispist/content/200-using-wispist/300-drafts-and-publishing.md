---
title: Drafts and publishing
type: concept
description: Wispdeck keeps Wispist draft data separate from live data, makes Current preview read-only, and preserves production documents across publish and rollback.
related:
  - wispist/getting-started/what-is-wispist
  - wispist/reference/wispist-json
  - wispist/problems/forbidden
---

Wispist data belongs to a site, not to one release. Releases select code and access policy; they do not each get a new production database.

Wispdeck binds each request as follows:

| View | Declaration | Namespace | Mutations |
| --- | --- | --- | --- |
| Public published site | Published release | Live | Per collection policy |
| Public site with no release | None | None | Denied |
| Private preview, Draft | Draft release | Draft | Per collection policy |
| Private preview, Current | Published release | Live | Always denied |

The Draft namespace remains stable across successive draft uploads for the same site, so ordinary iteration does not discard test data.

## Publishing changes code, not data

Publishing or rolling back atomically changes the release pointer used by the public origin. Existing live documents remain where they are.

In particular:

- Publishing the first release does not copy draft documents into live.
- Republishing preserves live documents.
- Rolling back code preserves live documents.
- Removing a collection declaration hides its documents without deleting them.
- Re-adding the declaration exposes those documents again.

Promotion is deliberately not implicit. Draft data can be incomplete, destructive, private, or nonsensical. A future copy or promotion feature must be an explicit management action.

## Current is a safe comparison view

When both a public release and a new draft exist, preview offers Current and Draft. Current loads public code and live data on the private preview origin, but Wispdeck sets an unconditional read-only binding. A collection declaration cannot relax it.

`wispist.mode` reports `live-preview` and `wispist.readOnly` is `true`, allowing the page to hide editing controls. Those values are only presentation hints; the server rejects mutations even if site code ignores them.

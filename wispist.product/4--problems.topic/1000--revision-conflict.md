---
title: Revision conflict
type: reference
description: HTTP 412 problem returned when a create-only ID exists or a replacement or deletion no longer matches the observed document revision.
related:
  - wispist/problems/overview
  - wispist/using-wispist/documents-and-collections
  - wispist/reference/browser-api
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/revision-conflict/
```

Status: `412 Precondition Failed`. Browser code: `revision_conflict`.

The mutation's HTTP precondition did not match current state:

- `If-None-Match: *` was used to create an ID that already exists.
- `If-Match` carried an older revision for replacement or deletion.

Fetch or wait for the latest document, reconcile the user's intent, then submit a new conditional mutation using that revision. Never loop blindly: another caller may have made a meaningful conflicting change.

The browser client's `replace`, `update`, and `delete` methods accept an observed document envelope so safe concurrency is the normal path.

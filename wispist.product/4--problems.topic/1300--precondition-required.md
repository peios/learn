---
title: Precondition required
type: reference
description: HTTP 428 problem returned when a Wispist replacement or deletion omits the conditional revision required for safe concurrency.
related:
  - wispist/problems/overview
  - wispist/problems/revision-conflict
  - wispist/using-wispist/documents-and-collections
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/precondition-required/
```

Status: `428 Precondition Required`. Browser code: `precondition_required`.

Wispist does not offer unconditional last-write-wins mutation. A selected-ID create requires `If-None-Match: *`. Replacing or deleting an existing document requires `If-Match` with the quoted observed revision.

Read the current document and use `replace`, `update`, or `delete` with that complete envelope. If the supplied revision is no longer current, the next response is [Revision conflict](~wispist/problems/revision-conflict).

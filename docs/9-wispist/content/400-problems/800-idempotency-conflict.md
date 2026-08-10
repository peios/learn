---
title: Idempotency conflict
type: reference
description: HTTP 409 problem returned when a generated-ID POST reuses a live idempotency key for a different request fingerprint.
related:
  - wispist/problems/overview
  - wispist/reference/http-api
  - wispist/problems/revision-conflict
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/idempotency-conflict/
```

Status: `409 Conflict`. Browser code: `idempotency_conflict`.

The `Idempotency-Key` was already used in this namespace for a different generated-ID POST. Wispist retains each successful key and response for at least 24 hours so a lost response can be retried safely.

If this is a retry, send exactly the same method, path, and document data. If it is a new logical create, generate a new strong random key. The built-in `collection.add` method does this automatically.

This problem concerns POST request identity. Concurrent document revisions use [Revision conflict](~wispist/problems/revision-conflict).

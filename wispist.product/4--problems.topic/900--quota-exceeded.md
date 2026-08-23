---
title: Quota exceeded
type: reference
description: HTTP 409 problem returned when a mutation would exceed a Wispist collection document count, namespace byte limit, or idempotency-record bound.
related:
  - wispist/problems/overview
  - wispist/reference/limits
  - wispist/problems/request-too-large
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/quota-exceeded/
```

Status: `409 Conflict`. Browser code: `quota_exceeded`.

The mutation is valid in isolation but would exceed a storage bound. The transactional check may cover collection document count, total live or draft document bytes, or the maximum number of unexpired idempotency records.

Delete data that is no longer needed, reduce the proposed document, or ask the operator to review installation policy. A release declaration may lower limits but cannot raise them.

A single request or document that exceeds its byte limit uses [Request too large](~wispist/problems/request-too-large).

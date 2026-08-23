---
title: Temporarily unavailable
type: reference
description: HTTP 503 problem returned when the Wispist store is busy, its bounded open-store cache is saturated, or an internal operation cannot safely complete.
related:
  - wispist/problems/overview
  - wispist/problems/rate-limited
  - wispist/reference/http-api
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/temporarily-unavailable/
```

Status: `503 Service Unavailable`. Browser code: `temporarily_unavailable`.

Wispist could not safely complete the operation. Expected transient causes include a busy SQLite store or temporary saturation of the bounded open-store cache. The response may include `Retry-After`.

Retry idempotent reads after a short backoff. Retry generated-ID POST only with the same idempotency key and identical request. Conditional replacements and deletions may be retried with the same observed revision; a committed competing change then becomes [Revision conflict](~wispist/problems/revision-conflict).

If the problem persists, give the operator the `X-Request-ID`. Wispist does not expose internal error text in the response.

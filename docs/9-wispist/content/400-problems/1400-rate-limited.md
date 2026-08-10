---
title: Rate limited
type: reference
description: HTTP 429 problem returned when a bounded Wispist request token bucket or concurrent change-stream allowance has been exhausted.
related:
  - wispist/problems/overview
  - wispist/reference/limits
  - wispist/problems/temporarily-unavailable
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/rate-limited/
```

Status: `429 Too Many Requests`. Browser code: `rate_limited`.

A read, mutation, generated-ID create, installation-wide request, or concurrent change stream exceeded its bounded allowance. `Retry-After` gives the minimum server-selected delay in seconds.

Wait for that delay and retry with backoff. Avoid tight loops, duplicate subscriptions, and unnecessary full-list refreshes. The built-in subscription client already reconnects with bounded exponential backoff.

Rate limiting is an availability control. It does not change collection policy or make public writes private.

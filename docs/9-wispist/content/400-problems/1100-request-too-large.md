---
title: Request too large
type: reference
description: HTTP 413 problem returned when a Wispist request body or document representation exceeds its configured byte allowance.
related:
  - wispist/problems/overview
  - wispist/reference/limits
  - wispist/problems/quota-exceeded
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/request-too-large/
```

Status: `413 Content Too Large`. Browser code: `request_too_large`.

The request body or `data` representation exceeds the active collection limit. Wispist limits the body before decoding and allows only a small fixed amount beyond the document limit for the JSON envelope.

Reduce the document or split independent records into separate documents. A release may request a higher collection limit only up to the operator's host maximum.

Total namespace storage exhaustion uses [Quota exceeded](~wispist/problems/quota-exceeded).

---
title: Invalid request
type: reference
description: HTTP 400 problem returned when a Wispist path, query, identifier, cursor, precondition combination, or JSON envelope is invalid.
related:
  - wispist/problems/overview
  - wispist/problems/invalid-json
  - wispist/reference/http-api
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/invalid-request/
```

Status: `400 Bad Request`. Browser code: `invalid_request`.

Wispist returns this problem when the request cannot be interpreted under the v1 resource contract. Examples include an unknown or repeated query parameter, invalid collection or document ID, non-canonical path, malformed cursor, unknown request-envelope member, or contradictory conditional headers.

This differs from [Invalid JSON](~wispist/problems/invalid-json): the JSON may be syntactically valid while its protocol envelope or request metadata is not.

Correct the request rather than retrying it unchanged. Use the browser client where possible; it constructs canonical paths, envelopes, pagination, and mutation preconditions.

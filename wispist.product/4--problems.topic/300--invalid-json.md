---
title: Invalid JSON
type: reference
description: HTTP 400 problem returned for malformed, ambiguous, non-object, deeply nested, invalid UTF-8, or otherwise disallowed document JSON.
related:
  - wispist/problems/overview
  - wispist/problems/invalid-request
  - wispist/using-wispist/documents-and-collections
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/invalid-json/
```

Status: `400 Bad Request`. Browser code: `invalid_json`.

The submitted document representation is not permitted JSON. Wispist rejects malformed or invalid UTF-8 input, a `data` root that is not an object, duplicate object member names, more than 32 nesting levels, keys longer than 256 UTF-8 bytes, and trailing JSON values.

Generate the body with a normal JSON serialiser and pass a non-null object to the browser client. Duplicate members must be fixed at the producer; Wispist does not choose which ambiguous value wins.

An oversized representation uses [Request too large](~wispist/problems/request-too-large) instead.

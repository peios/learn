---
title: Unsupported media type
type: reference
description: HTTP 415 problem returned when a Wispist document mutation does not declare an application/json request body.
related:
  - wispist/problems/overview
  - wispist/reference/http-api
  - wispist/problems/invalid-json
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/unsupported-media-type/
```

Status: `415 Unsupported Media Type`. Browser code: `unsupported_media_type`.

Document create and replacement bodies require:

```http
Content-Type: application/json
```

Media-type parameters such as `charset=utf-8` are accepted, but another base type or a missing header is not. Set the header and send the documented `{"data": {...}}` envelope.

JSON that has the correct media type but invalid content uses [Invalid JSON](~wispist/problems/invalid-json) or [Invalid request](~wispist/problems/invalid-request).

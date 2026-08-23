---
title: Not found
type: reference
description: HTTP 404 problem returned when a Wispist resource, declared collection, document, or retained store state is unavailable.
related:
  - wispist/problems/overview
  - wispist/reference/wispist-json
  - wispist/reference/http-api
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/not-found/
```

Status: `404 Not Found`. Browser code: `not_found`.

The requested resource is unavailable. A document may not exist, the active release may not declare the collection, or the path may not identify a v1 resource.

Wispist does not reveal hidden stored documents merely because an older release once declared them. Removing a declaration makes the collection unavailable without deleting its data.

For `get`, treat this as an absent document where that is valid application state. For an entire collection, inspect the declaration attached to the release serving this request.

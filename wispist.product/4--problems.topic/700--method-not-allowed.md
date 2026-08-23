---
title: Method not allowed
type: reference
description: HTTP 405 problem returned when the Wispist path identifies a known resource but that resource does not implement the request method.
related:
  - wispist/problems/overview
  - wispist/reference/http-api
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/method-not-allowed/
```

Status: `405 Method Not Allowed`. Browser code: `method_not_allowed`.

The path names a known Wispist resource, but its method is not supported. The `Allow` response header lists valid methods and is authoritative.

For example, a collection document resource supports `GET`, `HEAD`, `PUT`, and `DELETE`, while the change stream supports only `GET`. Use the route table in the [HTTP API reference](~wispist/reference/http-api) or the browser client.

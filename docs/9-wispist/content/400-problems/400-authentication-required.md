---
title: Authentication required
type: reference
description: HTTP 401 problem returned when collection policy requires an authenticated principal and the Wispist host supplied an anonymous caller.
related:
  - wispist/problems/overview
  - wispist/problems/forbidden
  - wispist/reference/wispist-json
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/authentication-required/
```

Status: `401 Unauthorized`. Browser code: `authentication_required`.

The collection operation is declared `authenticated`, but the host did not bind an authenticated principal. The response includes `WWW-Authenticate`.

Wispdeck's initial hosted-site integration supplies anonymous principals to public and preview JavaScript. A dashboard session or private preview cookie does not automatically become Wispist identity. Until a host identity integration is configured, change the operation to `anyone` only if public access is genuinely intended, or leave it inaccessible.

An authenticated principal that still lacks permission receives [Forbidden](~wispist/problems/forbidden).

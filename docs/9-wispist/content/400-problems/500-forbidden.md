---
title: Forbidden
type: reference
description: HTTP 403 problem returned when Wispist policy, origin enforcement, or a host read-only override denies an operation.
related:
  - wispist/problems/overview
  - wispist/problems/authentication-required
  - wispist/using-wispist/drafts-and-publishing
---

Canonical type:

```text
https://learn.peios.org/wispist/problems/forbidden/
```

Status: `403 Forbidden`. Browser code: `forbidden`.

The bound principal may not perform the operation. Common causes are:

- The collection operation is `nobody`.
- A mutation did not carry the exact bound site `Origin`, or Fetch Metadata identified it as cross-site.
- The request is using Wispdeck's Current preview, whose live-data binding is unconditionally read-only.
- A configured authorizer denied the current or proposed document.

Do not retry unchanged. Check `wispist.readOnly` to adjust Current-preview UI, and compare the active release's `wispist.json` with the operation being attempted. Client metadata is only a UI hint; the server remains authoritative.

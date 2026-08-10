---
title: wispist.json reference
type: reference
description: The complete v1 release declaration schema, collection-name grammar, access profiles, operation policies, and collection-specific limits.
related:
  - wispist/getting-started/build-a-shared-checklist
  - wispist/using-wispist/documents-and-collections
  - wispist/reference/limits
  - wispist/problems/forbidden
---

`wispist.json` is an optional file at the site archive root. It declares the collections exposed to browser code by that release.

The parser is strict:

- The file must be UTF-8 JSON no larger than 64 KiB.
- Duplicate object members and unknown fields are errors.
- `version` must be `1`.
- `collections` is required and may contain at most 32 entries.
- Collection limits may lower, but never raise, host defaults.
- Missing `wispist.json` means zero declared collections.

An invalid declaration rejects the complete upload. It never falls back to a permissive policy.

## Top-level object

| Member | Type | Required | Meaning |
| --- | --- | --- | --- |
| `version` | integer | yes | Protocol declaration version; exactly `1`. |
| `collections` | object | yes | Collection name to collection declaration. |

## Collection names

Names match:

```text
[a-z][a-z0-9_-]{0,47}
```

They are ASCII, case-sensitive, and compared byte-for-byte.

## Collection declaration

| Member | Type | Required | Meaning |
| --- | --- | --- | --- |
| `access` | string or object | yes | A built-in profile or all six operation policies. |
| `limits` | object | no | Lower document count and byte limits. |

### Shared profile

```json
{
  "access": "shared"
}
```

`shared` expands to `anyone` for `list`, `read`, `create`, `update`, `delete`, and `subscribe`. Every visitor can read and change the collection.

### Expanded access

```json
{
  "access": {
    "list": "anyone",
    "read": "anyone",
    "create": "nobody",
    "update": "nobody",
    "delete": "nobody",
    "subscribe": "anyone"
  }
}
```

Every operation must appear exactly once:

| Operation | Controls |
| --- | --- |
| `list` | Listing collection documents. |
| `read` | Reading one document and receiving its body in a subscription. |
| `create` | Generated-ID POST and selected-ID create. |
| `update` | Replacing an existing document. |
| `delete` | Deleting an existing document. |
| `subscribe` | Opening a change stream for the collection. |

Each value is one of:

| Value | Meaning |
| --- | --- |
| `anyone` | Permit every principal. |
| `authenticated` | Require an authenticated principal asserted by the host. |
| `nobody` | Deny the operation. |

Wispdeck initially supplies anonymous principals to ordinary hosted-site and preview JavaScript. Preview authorization grants access to the preview, not authenticated Wispist authority.

`read` and `list` are intentionally independent, as are `read` and `subscribe`.

### Collection limits

```json
{
  "limits": {
    "maxDocuments": 250,
    "maxDocumentBytes": 4096
  }
}
```

| Member | Type | Range | Default |
| --- | --- | --- | --- |
| `maxDocuments` | integer | 1 to host maximum | 1,000 |
| `maxDocumentBytes` | integer | 2 to host maximum | 32 KiB |

These limits apply to that collection. The namespace also has a total live or draft byte limit.

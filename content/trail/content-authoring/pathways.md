---
title: Pathways
type: concept
order: 20
description: Pathways are ordered sequences of pages that guide readers through a topic. They provide their own sidebar navigation and prev/next links.
---

A pathway is a curated reading order through existing pages. When a reader follows a pathway, the sidebar is replaced with the pathway's page list, and prev/next links appear at the bottom of each page.

## What pathways solve

Documentation sites organize pages by topic (categories), but readers often need to learn topics in a specific order. A "Getting Started" guide might span three categories. A security tutorial might touch identity, access control, and auditing.

Pathways let you define these cross-cutting reading orders without duplicating content or rearranging your category structure.

## Defining a pathway

Pathways are TOML files in the `pathways/` directory. In multi-product mode, they live in `pathways/product-slug/`.

Each file defines one pathway. The filename (minus `.toml`) becomes the pathway slug.

### Example: pathways/beginner.toml

```toml
name = "Getting Started"
description = "A guided introduction for new users."
featured = true
order = 1

pages = [
  "getting-started/introduction",
  "getting-started/installation",
  "configuration/basic-config",
  "guides/first-project",
]
```

## Pathway fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | Yes | -- | Display name shown on pathway cards and in the sidebar when the pathway is active. |
| `description` | string | No | -- | Short description shown on pathway listing pages and cards. |
| `featured` | boolean | No | `false` | When `true`, the pathway appears on the product index page. Non-featured pathways only appear on the dedicated pathways listing page. |
| `order` | integer | No | `0` | Sort position in pathway listings. Lower numbers appear first. Pathways with the same order are sorted alphabetically by name. |
| `pages` | list of strings | Yes | -- | Ordered list of page slugs. In multi-product mode, use slugs relative to the product (e.g., `identity/tokens` not `peios/identity/tokens`). |

## How pathway navigation works

Pathway navigation is entirely client-side, driven by a query parameter and a JSON manifest.

### Build time

Trail generates a `pathways.json` file in the site root. This manifest contains every pathway with its pages, resolved titles, and full slugs.

### Runtime

When a reader clicks a pathway link, the URL includes a `?pathway=slug` query parameter. For example:

```
/getting-started/introduction/?pathway=beginner
```

The pathway JavaScript:

1. Reads the `pathway` query parameter from the URL.
2. Fetches `pathways.json` and finds the matching pathway.
3. Finds the current page in the pathway's page list.
4. **Replaces the category sidebar** with the pathway's page list. The sidebar heading changes to the pathway name.
5. **Shows prev/next navigation** at the bottom of the page. Links include the `?pathway=slug` parameter so the reader stays in the pathway.

If the current page is not in the pathway, or if the pathway slug is invalid, the default category sidebar is shown and no prev/next links appear.

### Entering a pathway

Readers enter a pathway from:

- The **homepage** (in single-product mode), which shows featured pathways.
- The **product index page** (in multi-product mode), which shows featured pathways.
- The **pathways listing page** at `/pathways/` (or `/product-slug/pathways/`), which shows all pathways.

The entry link points to the first page in the pathway with the `?pathway=slug` parameter.

### Leaving a pathway

A reader leaves a pathway by clicking any link in the main content area, the top navigation, or the search results. Only links within the pathway sidebar and the prev/next navigation carry the `?pathway=slug` parameter.

## Multi-product pathways

In multi-product mode, each product has its own set of pathways. The pathway files live in `pathways/product-slug/`:

```
pathways/
  peios/
    security-fundamentals.toml
    admin-guide.toml
  trail/
    authoring-guide.toml
```

Page slugs in multi-product pathway files are relative to the product. If the product slug is `peios` and the pathway lists `identity/tokens`, Trail resolves it to `peios/identity/tokens`.

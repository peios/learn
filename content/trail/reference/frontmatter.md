---
title: Frontmatter Reference
type: reference
order: 20
description: Complete table of all YAML frontmatter fields supported by Trail, with types, defaults, and descriptions.
---

Every content page in Trail can include a YAML frontmatter block at the top of the file, delimited by `---` lines. This page documents every supported field.

## Frontmatter format

```yaml
---
title: Page Title
type: concept
order: 10
description: A brief summary of this page.
updated: 2026-03-15
draft: false
related:
  - category/other-page
  - category/another-page
---
```

The frontmatter block must be the first thing in the file. It starts and ends with a line containing exactly `---` followed by a newline. Everything between the delimiters is parsed as YAML.

If a file has no frontmatter block, it is still processed. The page will have no title, type, or other metadata.

## Field reference

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `title` | string | Yes | `""` | The page title. Displayed in the browser tab, breadcrumb navigation, sidebar links, category listings, search results, and the page heading. |
| `type` | string | No | `""` | The page type. Trail renders a colored badge for recognized values. Common values are `concept` and `how-to`. Arbitrary strings are rendered as-is without an icon. |
| `order` | integer | No | `0` | Sort position within the page's category. Lower numbers appear first. Pages with the same order are sorted alphabetically by slug. |
| `description` | string | No | `""` | A short summary of the page. Used in `<meta name="description">`, `og:description`, search result cards, and category listing cards. |
| `updated` | string | No | `""` | A date string displayed on the page as "Updated {date}". Trail does not parse or validate this value -- it is rendered as-is. Common formats: `2026-03-15`, `March 2026`. |
| `draft` | boolean | No | `false` | When `true`, the page is excluded from the build entirely. It does not appear in the rendered site, search index, category listings, sidebar navigation, or pathway navigation. |
| `related` | list of strings | No | `[]` | A list of page slugs rendered as a "See also" section at the bottom of the page. Each slug is resolved to a page title. Unresolved slugs are rendered using the raw slug as the title. |

## Field details

### title

The title is the most important frontmatter field. It appears in:

- The `<title>` tag (as "{title} -- {site title}")
- The `<h1>` heading on the page
- Breadcrumb navigation
- Category sidebar links
- Category listing cards
- Search results
- Pathway sidebar links
- Related page links
- The print-all page

Pages without a title will have empty text in all of these locations.

### type

Trail recognizes two type values with special rendering:

| Value | Badge text | Icon |
|---|---|---|
| `concept` | Concept | Book |
| `how-to` | How-to | Wrench |

Any other string is rendered as a plain badge without an icon. For example, `type: reference` renders a badge that says "reference".

The type also appears in search results to help readers distinguish between explanatory content and procedural guides.

### order

Pages within a category are sorted by `order` first, then alphabetically by slug. An explicit order of `0` is treated the same as an unset order.

A common convention is to use increments of 10:

```yaml
order: 10   # First page
order: 20   # Second page
order: 30   # Third page
```

This leaves room to insert pages later without renumbering.

### description

Keep descriptions under 160 characters for optimal display in search engine results. The description is also the first thing readers see in category listings and search results, so make it specific and informative.

### draft

Draft pages are filtered out during the content loading phase, before the build. They do not appear anywhere in the generated site. This is useful for work-in-progress pages that should not be published.

```yaml
draft: true
```

Remove the field or set it to `false` to publish the page.

### related

The `related` field takes full page slugs (including category prefix and product prefix in multi-product mode):

```yaml
# Single-product mode
related:
  - guides/installation
  - reference/api

# Multi-product mode (from a page in the "peios" product)
related:
  - peios/identity/tokens
  - peios/access-control/acls
```

Related pages are rendered in a "See also" section with a horizontal rule separator at the bottom of the page content.

---
title: Pages and Frontmatter
type: concept
description: Every page is a Markdown file with YAML frontmatter. The frontmatter controls the page's title, type, order, description, and relationships to other pages.
---

Trail content files are standard Markdown with YAML frontmatter. The frontmatter block appears at the top of the file, delimited by `---` lines.

## Anatomy of a page

```markdown
---
title: Understanding Tokens
type: concept
description: Tokens carry identity information through the system.
updated: 2026-03-15
draft: false
related:
  - identity/what-are-sids
  - access-control/understanding-access-control
---

The page body goes here. Standard Markdown syntax applies.

## Section heading

More content.
```

## Frontmatter fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `title` | string | Yes | -- | The page title. Displayed in the browser tab, breadcrumbs, sidebar, and search results. |
| `type` | string | No | -- | Page type label. Common values are `concept` and `how-to`. Displayed as a badge on the page and in listings. |
| `order` | integer | No | `0` | Controls sort position within the category. Lower numbers appear first. Pages with the same order are sorted alphabetically by slug. |
| `description` | string | No | -- | A short summary. Used in meta tags, search results, and category listings. |
| `updated` | string | No | -- | A date string (e.g., `2026-03-15`) displayed on the page as "Updated {date}". |
| `draft` | boolean | No | `false` | When `true`, the page is excluded from the build entirely. It does not appear in the site, search index, or pathway navigation. |
| `related` | list of strings | No | `[]` | Slugs of related pages. Rendered as a "See also" section at the bottom of the page. |

## How files become pages

Trail processes content files through this pipeline:

1. **Discovery.** Trail walks the `content/` directory (or `content/product-slug/` in multi-product mode) and finds all `.md` files.
2. **Frontmatter parsing.** The YAML block between `---` delimiters is parsed into page metadata.
3. **Draft filtering.** Pages with `draft: true` are skipped.
4. **Slug derivation.** The file's path relative to the content root, minus the `.md` extension, becomes the slug. Forward slashes are used regardless of OS.
5. **Category assignment.** The first path component of the slug is the category name.
6. **Markdown rendering.** The body is converted to HTML using Goldmark with GFM tables, strikethrough, and auto-heading IDs.
7. **Post-processing.** The HTML passes through transforms for admonitions, tab groups, mermaid diagrams, inter-page links, table wrapping, and anchor link injection.

## Page types

The `type` field is a free-form string, but Trail renders badges for two recognized values:

| Type | Badge | Icon | Use for |
|---|---|---|---|
| `concept` | "Concept" | Book icon | Explanations, background, mental models |
| `how-to` | "How-to" | Wrench icon | Step-by-step procedures |

Other type values are rendered as-is without an icon. Omitting `type` produces no badge.

## Reading time

Trail estimates reading time from the word count of the Markdown body (200 words per minute). This appears next to the type badge on the rendered page.

## Headings and table of contents

Trail extracts `h2` and `h3` headings from the rendered HTML. These headings populate:

- The **"On this page"** sidebar on wide screens (right side)
- A **collapsible "On this page"** section on narrower screens (above the content)

Heading IDs are generated automatically from the heading text (Goldmark's auto-heading-ID feature). Each heading also receives a `#` anchor link that appears on hover.

## Related pages

The `related` field accepts a list of page slugs. Trail resolves each slug to a page title and renders a "See also" section at the bottom of the page.

```yaml
related:
  - identity/what-are-sids
  - identity/how-tokens-work
```

If a slug does not match any page, it still appears in the list but uses the raw slug as the title. This can help identify broken references during development.

---
title: Multi-Product Mode
type: concept
description: A single Trail site can host documentation for multiple products, each with its own categories, pathways, and content hierarchy.
---

Multi-product mode lets a single Trail site serve documentation for multiple products under one domain. Each product has its own content directory, category ordering, pathway definitions, and index page.

## Enabling multi-product mode

Multi-product mode activates automatically when `trail.toml` contains at least one `[[products]]` entry:

```toml
title = "Acme Documentation"

[[products]]
name = "Widget"
slug = "widget"
description = "The Widget platform."
order = 1

[[products]]
name = "Gadget"
slug = "gadget"
description = "The Gadget toolkit."
order = 2
```

## Directory structure

In multi-product mode, content and pathways are organized by product:

```
my-docs/
  trail.toml
  content/
    widget/                 # Content for the Widget product
      getting-started/
        introduction.md
        installation.md
      reference/
        api.md
    gadget/                 # Content for the Gadget product
      overview/
        what-is-gadget.md
      configuration/
        settings.md
  pathways/
    widget/                 # Pathways for Widget
      beginner.toml
    gadget/                 # Pathways for Gadget
      quick-start.toml
```

The directory names under `content/` and `pathways/` must match the `slug` field of the corresponding product.

## URL structure

Product slugs are the first segment of every URL:

| File | URL |
|---|---|
| `content/widget/getting-started/introduction.md` | `/widget/getting-started/introduction/` |
| `content/gadget/overview/what-is-gadget.md` | `/gadget/overview/what-is-gadget/` |

Each product also gets an index page at its root URL (e.g., `/widget/`).

## Homepage

In multi-product mode, the homepage displays a grid of product cards instead of a category grid. Each card shows the product name, description, and page count. Clicking a card navigates to the product index page.

## Product index pages

Each product has an index page at `/product-slug/`. This page shows:

1. **Featured pathways** (if any) in a horizontal scrollable row at the top.
2. **Categories** in a grid, each showing the category title and up to three page links.

## Category ordering

Each product has its own `category_order` field:

```toml
[[products]]
name = "Widget"
slug = "widget"
order = 1
category_order = ["getting-started", "guides", "reference"]

[[products]]
name = "Gadget"
slug = "gadget"
order = 2
category_order = ["overview", "configuration"]
```

Categories not listed in `category_order` appear after the listed ones, sorted by the order they were discovered during the file walk.

## Product ordering

Products are sorted on the homepage by the `order` field. Products with `order = 0` (or no order specified) sort after products with explicit order values. Among products with equal order, sorting is alphabetical by name.

```toml
[[products]]
name = "Alpha"
slug = "alpha"
order = 1           # Appears first

[[products]]
name = "Beta"
slug = "beta"
order = 2           # Appears second

[[products]]
name = "Gamma"
slug = "gamma"
                    # order defaults to 0, appears last
```

## Pathways in multi-product mode

Pathways are scoped to products. A pathway file at `pathways/widget/beginner.toml` belongs to the Widget product.

Page slugs in pathway files are relative to the product. If the pathway lists `getting-started/introduction`, Trail resolves it to `widget/getting-started/introduction`.

```toml
# pathways/widget/beginner.toml
name = "Beginner Guide"
description = "Start here."
featured = true
order = 1
pages = [
  "getting-started/introduction",
  "getting-started/installation",
  "reference/api",
]
```

The pathways listing page for a product is at `/product-slug/pathways/`.

## Breadcrumbs

Pages in multi-product mode have an additional breadcrumb level:

```
Home / Widget / Getting started / Introduction
```

The product name links to the product index page, and the category name links to the category listing page.

## Navigation bar

The navigation bar is global (not per-product). Use `[[nav]]` entries to provide quick access to each product:

```toml
[[nav]]
label = "Widget"
url = "/widget/"

[[nav]]
label = "Gadget"
url = "/gadget/"
```

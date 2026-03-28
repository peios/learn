---
title: trail.toml Reference
type: reference
order: 10
description: Complete reference for every field in the trail.toml configuration file, covering both single-product and multi-product modes.
---

The `trail.toml` file is the sole configuration file for a Trail site. It lives at the root of your project directory.

## Minimal configuration

```toml
title = "My Docs"
```

The only required field is `title`. Everything else has sensible defaults or is optional.

## Complete example

```toml
title = "Acme Documentation"
description = "Everything you need to know about Acme products."
base_url = "https://docs.acme.com"
repo_url = "https://github.com/acme/docs"
favicon = "/images/favicon.ico"
head_extra = '<link rel="stylesheet" href="/custom.css">'
announcement = "Version 3.0 has been released!"

[[nav]]
label = "Product A"
url = "/product-a/"

[[nav]]
label = "Product B"
url = "/product-b/"

[[products]]
name = "Product A"
slug = "product-a"
description = "The main product."
order = 1
category_order = ["getting-started", "guides", "reference"]

[[products]]
name = "Product B"
slug = "product-b"
description = "The companion tool."
order = 2
category_order = ["overview", "configuration"]
```

## Top-level fields

| Field | Type | Default | Description |
|---|---|---|---|
| `title` | string | -- | **Required.** The site title. Displayed in the header, browser tab titles, and Open Graph tags. |
| `description` | string | `""` | Site-level description. Used in meta tags and the homepage hero section. |
| `base_url` | string | `""` | The canonical base URL of the deployed site (e.g., `https://docs.example.com`). Used for canonical tags, Open Graph URLs, and the sitemap. No trailing slash. |
| `repo_url` | string | `""` | The repository URL (e.g., `https://github.com/org/repo`). When set, an "Edit this page on GitHub" link appears at the bottom of every page. The link points to `{repo_url}/edit/main/content/{slug}.md`. |
| `favicon` | string | `""` | Path to the favicon file. If set, Trail adds a `<link rel="icon">` tag. The file should be placed in the `static/` directory. |
| `head_extra` | string | `""` | Raw HTML injected into the `<head>` of every page. Use for custom stylesheets, analytics scripts, or other head elements. |
| `announcement` | string | `""` | Text displayed in a banner at the top of every page. The banner is blue with white text and has a dismiss button. Dismissal persists in localStorage keyed by the announcement text, so changing the text resets the dismissal. |
| `category_order` | list of strings | `[]` | *Single-product mode only.* Controls the display order of categories on the homepage and sidebar. Values are directory names (e.g., `"getting-started"`). Categories not listed appear after the ordered ones, sorted by discovery order. |

## Navigation: [[nav]]

The `[[nav]]` array defines links in the top navigation bar. Each entry has two fields:

| Field | Type | Description |
|---|---|---|
| `label` | string | The display text for the link. |
| `url` | string | The link URL. Can be an absolute path (`/product-a/`) or an external URL (`https://example.com`). |

```toml
[[nav]]
label = "Guides"
url = "/guides/"

[[nav]]
label = "GitHub"
url = "https://github.com/org/repo"
```

Navigation links appear in the header on desktop. On mobile, they move to the hamburger menu.

## Products: [[products]]

The `[[products]]` array enables multi-product mode. When at least one product is defined, Trail expects content in `content/product-slug/` subdirectories and pathways in `pathways/product-slug/`.

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | -- | **Required.** Display name for the product. |
| `slug` | string | -- | **Required.** URL-safe identifier. Must match the directory name under `content/` and `pathways/`. |
| `description` | string | `""` | Product description. Displayed on the homepage product card and the product index page. |
| `order` | integer | `0` | Sort position on the homepage. Lower numbers first. Products with `0` sort after products with explicit order values. Products with equal order are sorted alphabetically by name. |
| `category_order` | list of strings | `[]` | Controls category display order for this product. Same behavior as the top-level `category_order` but scoped to the product. |

```toml
[[products]]
name = "Trail"
slug = "trail"
description = "Static site generator for documentation."
order = 1
category_order = ["getting-started", "content-authoring", "configuration", "features", "reference"]
```

See [multi-product mode](~trail/configuration/multi-product) for the full explanation of how products work.

## Single-product vs. multi-product mode

Trail operates in one of two modes based on whether `[[products]]` is defined:

| Aspect | Single-product | Multi-product |
|---|---|---|
| Content location | `content/category/page.md` | `content/product-slug/category/page.md` |
| Pathways location | `pathways/name.toml` | `pathways/product-slug/name.toml` |
| Category ordering | Top-level `category_order` | Per-product `category_order` |
| Homepage | Categories grid | Products grid |
| URL structure | `/category/page/` | `/product-slug/category/page/` |

The two modes are mutually exclusive. If `[[products]]` is defined, the top-level `category_order` is ignored.

---
title: Project Structure
type: concept
description: A Trail site is organized into four directories — trail.toml for configuration, content/ for pages, pathways/ for learning paths, and static/ for assets.
---

A Trail project follows a fixed directory layout. There is no scaffolding command; you create the directories yourself.

## Directory layout

```
my-docs/
  trail.toml              # Site configuration (required)
  content/                # Markdown pages (required)
    getting-started/      # Category directory
      introduction.md     # Page
      installation.md     # Page
    reference/
      api.md
  pathways/               # Learning pathway definitions (optional)
    beginner.toml
    advanced.toml
  static/                 # Static assets copied to output root (optional)
    images/
      logo.png
  _site/                  # Build output (generated, not checked in)
```

## trail.toml

The configuration file at the project root. It defines site metadata (title, description, base URL), navigation links, product definitions for multi-product mode, and category ordering.

This is the only required file besides content. A minimal `trail.toml` needs only `title`:

```toml
title = "My Docs"
```

See the [trail.toml reference](~trail/configuration/trail-toml) for every available field.

## content/

All Markdown pages live here. The directory structure determines the site's information architecture:

- **First-level subdirectories** are categories. A directory named `getting-started/` creates a category titled "Getting started".
- **Markdown files** within a category are pages. The filename (minus `.md`) becomes the page slug.
- **Frontmatter** in each file provides the page title, type, order, description, and other metadata.

In multi-product mode, content is nested one level deeper: `content/product-slug/category/page.md`.

Pages at the root of `content/` (not in any subdirectory) are uncategorized. They appear in the site but have no category sidebar.

### How slugs are derived

The slug is the file's path relative to the content directory, with the `.md` extension removed. In multi-product mode, the product slug is prepended.

| File path | Mode | Slug |
|---|---|---|
| `content/guides/install.md` | Single-product | `guides/install` |
| `content/peios/identity/tokens.md` | Multi-product | `peios/identity/tokens` |
| `content/setup.md` | Single-product | `setup` |

The slug determines the page's URL: a page with slug `guides/install` is served at `/guides/install/`.

### How categories are derived

The category is the first directory component of the path relative to the content root (or product root in multi-product mode).

| File path | Category |
|---|---|
| `content/guides/install.md` | `guides` |
| `content/guides/configure.md` | `guides` |
| `content/reference/api.md` | `reference` |

Category titles are generated automatically by replacing hyphens with spaces and capitalizing the first letter. The directory name `getting-started` becomes the display title "Getting started".

## pathways/

Pathway definitions are TOML files, one per pathway. In single-product mode they live directly in `pathways/`. In multi-product mode they are nested: `pathways/product-slug/pathway-name.toml`.

The filename (minus `.toml`) becomes the pathway slug. A file named `beginner.toml` creates a pathway with slug `beginner`.

See [pathways](~trail/content-authoring/pathways) for the TOML format and how pathway navigation works.

## static/

Files in `static/` are copied verbatim to the output directory root. Use this for images, downloadable files, favicons, or any other asset that should be served as-is.

A file at `static/images/logo.png` is available at `/images/logo.png` in the built site.

## _site/ (output)

The default output directory. Trail deletes and recreates this directory on every build. Do not put hand-written files here.

The output directory can be changed with the `--output` flag:

```
trail build --output dist
```

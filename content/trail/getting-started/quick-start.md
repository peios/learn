---
title: Quick Start
type: how-to
order: 20
description: Create a Trail documentation site from scratch, build it, and serve it locally in under five minutes.
---

This guide walks through creating a minimal Trail site, building it, and serving it locally.

## Prerequisites

Trail is distributed as a single Go binary. Install it with:

```
go install github.com/peios/trail@latest
```

Verify the installation:

```
trail help
```

## Create a site

A Trail site needs two things: a `trail.toml` configuration file and at least one Markdown file in a `content/` directory.

### 1. Create the project directory

```
mkdir my-docs && cd my-docs
```

### 2. Create trail.toml

Create a file named `trail.toml` in the project root:

```toml
title = "My Documentation"
description = "Documentation for my project."
base_url = "https://docs.example.com"
```

### 3. Create a content file

Content files live in subdirectories of `content/`. The subdirectory name becomes the category.

```
mkdir -p content/getting-started
```

Create `content/getting-started/introduction.md`:

```markdown
---
title: Introduction
type: concept
order: 10
description: An overview of the project and what it does.
---

Welcome to the documentation. This is the first page.

## What this project does

It does useful things.

## Next steps

Read the other pages in this section to learn more.
```

### 4. Build the site

```
trail build
```

Trail writes the output to `_site/` by default. The command prints a summary:

```
Built 1 pages in 1 categories with 0 pathways -> _site
```

### 5. Serve locally

```
trail serve
```

Open `http://localhost:3000` in a browser. The dev server watches for file changes and reloads the browser automatically.

## Add more content

Create additional files in `content/`. Each subdirectory becomes a category. Files within a category are sorted by the `order` field in their frontmatter.

```
content/
  getting-started/
    introduction.md       (order: 10)
    installation.md       (order: 20)
  configuration/
    basic-config.md       (order: 10)
    advanced-config.md    (order: 20)
```

## Control category ordering

By default, categories appear in the order Trail encounters them on disk. To control the order, add `category_order` to `trail.toml`:

```toml
title = "My Documentation"
description = "Documentation for my project."
base_url = "https://docs.example.com"
category_order = ["getting-started", "configuration"]
```

The values in `category_order` are directory names, not display titles. Trail converts directory names to display titles automatically (e.g., `getting-started` becomes "Getting started").

## Add a pathway

Pathways are ordered sequences of pages. Create a `pathways/` directory and add a TOML file:

```
mkdir pathways
```

Create `pathways/beginner.toml`:

```toml
name = "Beginner Guide"
description = "Start here if you are new."
featured = true
order = 1

pages = [
  "getting-started/introduction",
  "configuration/basic-config",
]
```

Rebuild the site. The homepage now shows the pathway, and clicking it navigates through the listed pages in order with prev/next links.

## Next steps

- Read about the full [project structure](~trail/getting-started/project-structure) to understand what each directory does.
- See the [trail.toml reference](~trail/configuration/trail-toml) for all available configuration options.
- Learn about [pages and frontmatter](~trail/content-authoring/pages-and-frontmatter) for the complete set of frontmatter fields.

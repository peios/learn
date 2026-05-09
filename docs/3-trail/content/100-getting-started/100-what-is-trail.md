---
title: What Is Trail
type: concept
description: Trail is a static site generator purpose-built for documentation. It produces fast, searchable sites with pathway-based navigation, dark mode, and multi-product support.
---

Trail is a static site generator designed specifically for documentation sites. It takes a directory of Markdown files and a `trail.toml` configuration file and produces a complete static website with search, dark mode, pathway navigation, and responsive design.

## Why Trail exists

General-purpose static site generators like Hugo require extensive configuration and theme selection before you can publish documentation. Documentation-specific tools like Docusaurus pull in a Node.js runtime and hundreds of dependencies. MkDocs requires a Python environment and plugin ecosystem.

Trail takes a different approach. It is a single Go binary with no runtime dependencies. Every feature a documentation site needs is built in: fuzzy search, dark mode, syntax highlighting, learning pathways, and multi-product support. There is no theme to install, no plugin system to learn, and no package manager to manage.

## Key features

| Feature | Description |
|---|---|
| **Learning pathways** | Define ordered sequences of pages that guide readers through a topic. Pathways replace the sidebar with their own page list and add prev/next navigation. |
| **Multi-product support** | A single site can host documentation for multiple products, each with its own categories, pathways, and content hierarchy. |
| **Built-in search** | Trail generates a search index at build time. The client uses Fuse.js for instant fuzzy search with keyboard navigation and result highlighting. |
| **Dark mode** | System preference detection with a manual toggle. Theme choice persists in localStorage. A no-flash script prevents the white flash on page load. |
| **Syntax highlighting** | Code blocks are highlighted at build time using Chroma with the Dracula theme. Every code block has a copy button. |
| **Admonitions** | GitHub-style blockquote syntax for NOTE, WARNING, IMPORTANT, TIP, and CAUTION callouts. |
| **Tab groups** | Group related content into tabbed panels using HTML comment markers. |
| **Mermaid diagrams** | Fenced code blocks with the `mermaid` language tag render as diagrams. Diagrams re-render on theme toggle. |
| **Live reload** | The dev server watches for file changes and reloads the browser via Server-Sent Events. |
| **SEO** | Open Graph tags, canonical URLs, sitemap.xml, and robots.txt are generated automatically. |

## How it compares

| | Trail | Hugo | Docusaurus | MkDocs |
|---|---|---|---|---|
| **Runtime** | Single binary | Single binary | Node.js | Python |
| **Config** | One TOML file | TOML + theme config | JS config + plugins | YAML + plugins |
| **Search** | Built-in (Fuse.js) | Requires plugin/service | Built-in (Algolia or local) | Requires plugin |
| **Learning paths** | Built-in pathways | Manual | Manual sidebar ordering | Manual |
| **Multi-product** | Built-in | Requires module system | Multi-instance or plugin | Manual |
| **Dark mode** | Built-in | Theme-dependent | Built-in | Theme-dependent |
| **Dependencies** | Zero | Zero | ~1000+ npm packages | Python packages |

## How it works

Trail reads your project directory and processes it in a single pass:

1. **Parse configuration.** Trail reads `trail.toml` for site metadata, navigation, product definitions, and category ordering.
2. **Load content.** Trail walks the `content/` directory, parses YAML frontmatter and Markdown bodies, and organizes pages into categories.
3. **Load pathways.** Trail reads `.toml` files from the `pathways/` directory and resolves page references.
4. **Build output.** Trail converts Markdown to HTML, applies transforms (admonitions, tabs, mermaid, inter-page links), wraps content in templates, and writes everything to the output directory.
5. **Generate assets.** Trail writes the search index, sitemap, robots.txt, JavaScript assets, and copies the `static/` directory.

The output is a self-contained directory of HTML, CSS, and JavaScript files ready to deploy to any static hosting provider.

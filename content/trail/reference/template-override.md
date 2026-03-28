---
title: Built-in Templates
type: concept
order: 30
description: Trail uses a fixed set of Go HTML templates to render every page type. This page documents what each template renders and the data it receives.
---

Trail has a fixed set of built-in templates. There is no theme system and no way to override templates through configuration. The templates are embedded in the Trail binary.

This page documents each template, what it renders, and the data available to it. This is useful for understanding Trail's output structure and for contributing to Trail itself.

## Template architecture

All templates share a common base template that renders the HTML shell: `<html>`, `<head>`, `<body>`, the header, footer, scripts, and stylesheets. Each page type defines two template blocks:

- `title` -- the contents of the `<title>` tag.
- `content` -- the main content area between the header and footer.

The base template also defines optional blocks for `meta_description` and `canonical` that page templates can override.

## Template list

Trail defines eight templates:

| Template | URL pattern | Purpose |
|---|---|---|
| **Page** | `/{slug}/` | Individual content pages |
| **Homepage** | `/` | Site homepage |
| **Category** | `/{category}/` or `/{product}/{category}/` | Category listing pages |
| **Product** | `/{product}/` | Product index pages (multi-product only) |
| **Pathways** | `/pathways/` | Pathways listing page (single-product) |
| **Product Pathways** | `/{product}/pathways/` | Pathways listing page (multi-product) |
| **404** | `/404.html` | Not found page |
| **Print** | `/print/` | All pages in one document |

## Base template

The base template renders the common elements on every page:

- **Dark mode script** -- inline in `<head>`, prevents flash.
- **Tailwind CSS** -- loaded from CDN.
- **Custom styles** -- Tailwind CSS extensions for prose, admonitions, tabs, print styles.
- **Announcement bar** -- conditional, dismissible, persisted in localStorage.
- **Header** -- site title (linked to homepage), nav links, search input, dark mode toggle, mobile menu button.
- **Mobile menu** -- hidden by default, toggled by hamburger button. Contains nav links and mobile search.
- **Main content** -- the `{{template "content" .}}` block.
- **Back to top button** -- appears after scrolling 400px.
- **Footer** -- site title and "Built with Trail" link.
- **Scripts** -- Mermaid (CDN), Fuse.js (CDN), live reload, pathway, theme, search, mobile, copy code, tabs, scroll spy, back to top, highlight, font size.

## Page template

Renders individual content pages. This is the most complex template.

**Layout:** Three-column on wide screens (category sidebar, content, "On this page" outline). Two-column on large screens (sidebar + content). Single-column on mobile.

**Content includes:**

- Breadcrumbs (Home / Product / Category / Page title)
- Collapsible "On this page" outline (visible on screens narrower than xl)
- Type badge, reading time, and updated date
- Page title as `<h1>`
- Rendered HTML content in a `.prose` container
- Related pages section ("See also")
- Edit on GitHub link (if `repo_url` is configured)
- Pathway prev/next navigation (hidden by default, shown by pathway JS)
- Right sidebar with font size controls and "On this page" outline (visible on xl screens)

**Category sidebar:** Shows all pages in the current category. The current page is highlighted. When a pathway is active, the sidebar content is replaced by the pathway's page list via client-side JavaScript.

## Homepage template

**Multi-product mode:** Displays a hero section with the site title and description, followed by a grid of product cards. Each card shows the product name, description, and page count.

**Single-product mode:** Displays the hero section followed by a grid of category cards. Each card shows the category title and up to three page links, with a "See all N articles" link for categories with more than three pages.

## Category template

Lists all pages in a category. Each page is shown as a card with:

- Type badge
- Page title
- Description (if set)

Pages are sorted by the `order` frontmatter field, then alphabetically.

## Product template

Shown at `/{product}/`. Displays:

- Breadcrumbs (Home / Product)
- Product name and description
- Featured pathways in a horizontal scrollable row (if any pathways have `featured = true`)
- "View all" link to the pathways page (if there are non-featured pathways)
- Category grid (same format as single-product homepage)

## Pathways and Product Pathways templates

List all pathways as cards in a grid. Each card shows the pathway name, description, and page count. Clicking a card navigates to the first page of the pathway with the `?pathway=slug` parameter.

## 404 template

A simple centered page showing "404", "This page doesn't exist.", and a link back to the homepage.

## Print template

Renders all pages in a single document for printing or offline reading. The title is "{Site Title} -- Complete Reference". Each page is rendered as a section with:

- Type badge and category label
- Page title as `<h2>`
- Full rendered HTML content
- A horizontal rule separator

Print-specific CSS hides the header, footer, sidebar, search, theme toggle, and other interactive elements.

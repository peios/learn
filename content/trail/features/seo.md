---
title: SEO
type: concept
order: 40
description: Trail generates Open Graph tags, canonical URLs, meta descriptions, a sitemap, and robots.txt automatically.
---

Trail generates standard SEO metadata for every page without any additional configuration beyond setting `base_url` in `trail.toml`.

## Open Graph tags

Every page includes Open Graph meta tags:

| Tag | Value |
|---|---|
| `og:title` | Page title (or site title for the homepage) |
| `og:site_name` | Site title from `trail.toml` |
| `og:description` | Page description if set, otherwise site description |
| `og:url` | Base URL from `trail.toml` (if set) |
| `og:type` | `article` |

These tags control how the page appears when shared on social media, messaging apps, and other platforms that read Open Graph metadata.

## Meta descriptions

Trail sets the `<meta name="description">` tag from two sources, in order of priority:

1. **Page-level:** The `description` field in the page's YAML frontmatter.
2. **Site-level:** The `description` field in `trail.toml`.

If neither is set, the meta description tag is omitted.

Writing good descriptions is important for search engine result pages (SERPs). Keep them under 160 characters and make them specific to the page content.

## Canonical URLs

When `base_url` is set in `trail.toml`, content pages include a canonical link tag:

```html
<link rel="canonical" href="https://docs.example.com/guides/install/">
```

Canonical URLs tell search engines which URL is the authoritative version of the page. This is important if your content is accessible from multiple URLs or domains.

The homepage and non-content pages (category pages, pathways pages, 404) do not include canonical tags.

## Browser tab titles

Page titles follow the pattern:

```
{Page Title} - {Site Title}
```

The homepage uses just the site title. This pattern helps readers identify your site in browser tabs and bookmarks.

## sitemap.xml

Trail generates a `sitemap.xml` file in the output root. It includes:

- The homepage URL
- All category index page URLs
- All content page URLs

Each URL uses the `base_url` from `trail.toml` as its prefix. The sitemap follows the standard [Sitemaps protocol](https://www.sitemaps.org/) format.

Example output:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://docs.example.com/</loc></url>
  <url><loc>https://docs.example.com/guides/</loc></url>
  <url><loc>https://docs.example.com/guides/install/</loc></url>
  <url><loc>https://docs.example.com/guides/configure/</loc></url>
</urlset>
```

## robots.txt

Trail generates a `robots.txt` file that allows all crawlers and points to the sitemap:

```
User-agent: *
Allow: /
Sitemap: https://docs.example.com/sitemap.xml
```

The sitemap URL uses the `base_url` from `trail.toml`.

## What Trail does not do

Trail's SEO features cover the fundamentals. It does not generate:

- **Structured data** (JSON-LD, Schema.org)
- **Twitter Card tags** (use `head_extra` to add these)
- **RSS/Atom feeds**
- **Last-modified dates in the sitemap** (pages have an `updated` field, but it is not included in the sitemap)

If you need these, use the `head_extra` field in `trail.toml` for global additions, or add raw HTML in your Markdown content for page-specific metadata.

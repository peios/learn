---
title: Navigation and Theming
type: how-to
order: 30
description: Configure the navbar links, announcement bar, favicon, head injection, and repository URL for edit links.
---

Trail's visual appearance is built in and not customizable through themes or templates. However, several configuration options let you control the navigation, branding, and page-level additions.

## Navbar links

The `[[nav]]` array in `trail.toml` defines links in the top navigation bar:

```toml
[[nav]]
label = "Guides"
url = "/guides/"

[[nav]]
label = "API"
url = "/reference/api/"

[[nav]]
label = "GitHub"
url = "https://github.com/org/repo"
```

Links can point to internal pages (using absolute paths) or external URLs. On desktop, links display horizontally in the header. On mobile, they move to the hamburger menu.

There is no limit on the number of nav links, but more than five or six may crowd the header on smaller desktop screens.

## Announcement bar

The `announcement` field adds a blue banner across the top of every page:

```toml
announcement = "Version 3.0 has been released! See the migration guide."
```

The banner includes a dismiss button. When a reader dismisses it, the dismissal is stored in localStorage keyed by the exact announcement text. This means:

- Changing the announcement text causes it to reappear for all readers.
- Setting `announcement` to an empty string (or removing the field) removes the banner entirely.

The announcement field accepts plain text. HTML is not rendered.

## Favicon

The `favicon` field sets the page icon:

```toml
favicon = "/images/favicon.ico"
```

Place the favicon file in the `static/` directory. A file at `static/images/favicon.ico` is served at `/images/favicon.ico`.

Trail adds a `<link rel="icon" href="...">` tag to every page when this field is set.

## Head injection

The `head_extra` field injects raw HTML into the `<head>` of every page:

```toml
head_extra = '<link rel="stylesheet" href="/custom.css"><script async src="https://analytics.example.com/script.js"></script>'
```

This is useful for:

- Custom CSS overrides
- Analytics scripts
- Additional meta tags
- Web font links
- Verification tags for search engines

The content is inserted as-is, so it must be valid HTML.

For multi-line values in TOML, use triple-quoted strings:

```toml
head_extra = '''
<link rel="stylesheet" href="/custom.css">
<script async src="https://analytics.example.com/script.js"></script>
'''
```

## Repository URL and edit links

The `repo_url` field enables "Edit this page on GitHub" links at the bottom of every content page:

```toml
repo_url = "https://github.com/acme/docs"
```

Trail constructs the edit URL as:

```
{repo_url}/edit/main/content/{page-slug}.md
```

This assumes:

- The repository is on GitHub (the "edit" URL format is GitHub-specific).
- The default branch is `main`.
- Content files are in a `content/` directory at the repository root.

If your repository uses a different branch name or directory structure, the edit links may point to incorrect locations. There is currently no configuration to customize the edit URL pattern.

## Site title

The `title` field appears in multiple places:

- The header (top-left, linked to the homepage)
- Browser tab titles (as a suffix: "Page Title -- Site Title")
- Open Graph `og:site_name` meta tag
- The footer

```toml
title = "Acme Documentation"
```

## Site description

The `description` field is used for:

- The homepage hero section subtitle
- The `og:description` and `meta description` tags on pages that do not have their own description
- The site-wide meta description fallback

```toml
description = "Everything you need to know about Acme products."
```

Pages with their own `description` frontmatter field override the site-level description in meta tags.

## Base URL

The `base_url` field is the canonical root URL of the deployed site:

```toml
base_url = "https://docs.acme.com"
```

It is used for:

- Canonical `<link>` tags on content pages
- `og:url` meta tags
- The `Sitemap` directive in `robots.txt`
- URL entries in `sitemap.xml`

Do not include a trailing slash. Trail handles path joining internally.

If `base_url` is empty, canonical tags and Open Graph URLs are omitted. The sitemap and robots.txt are still generated but with empty base URLs.

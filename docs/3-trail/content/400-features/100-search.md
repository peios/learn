---
title: Search
type: concept
description: Trail builds a search index at build time and provides instant fuzzy search powered by Fuse.js, with keyboard navigation and result highlighting.
---

Trail includes a complete search implementation with no external services. The search index is generated at build time, and the client performs fuzzy matching entirely in the browser.

## How the search index is built

During `trail build`, Trail creates a `search-index.json` file in the output directory. Each page contributes one entry with the following fields:

| Field | Source |
|---|---|
| `title` | Page frontmatter `title` |
| `slug` | Derived from file path |
| `category` | First directory component of the slug |
| `type` | Page frontmatter `type` |
| `description` | Page frontmatter `description` |
| `content` | First 500 characters of the Markdown body, stripped of formatting |

The content field is truncated to keep the index size reasonable for client-side loading. Titles are weighted higher than content in search ranking.

## Client-side search

Search is powered by [Fuse.js](https://www.fusejs.io/), a lightweight fuzzy search library loaded from CDN. On page load, the browser fetches `search-index.json` and initializes a Fuse instance.

The search configuration:

| Parameter | Value |
|---|---|
| Threshold | 0.3 (fairly strict fuzzy matching) |
| Min match length | 2 characters |
| Title weight | 2x |
| Content weight | 1x |
| Max results | 8 |

## Search interface

The search input is in the top navigation bar on desktop screens. On mobile, it appears in the hamburger menu.

### Desktop

The search input shows the placeholder text "Search... (/)" indicating the keyboard shortcut. Results appear in a dropdown below the input, showing:

- Page title (bold)
- Description (if present)
- Page type label and category

### Mobile

The mobile search is a separate input in the mobile menu with its own results dropdown. It shows up to 6 results.

## Keyboard navigation

| Key | Action |
|---|---|
| `/` | Focus the search input from anywhere on the page (only when no other input is focused) |
| Type text | Start searching (results appear after 2+ characters) |
| `Arrow Down` or `Tab` | Move to the next result |
| `Arrow Up` or `Shift+Tab` | Move to the previous result |
| `Enter` | Navigate to the highlighted result |
| `Escape` | Close the results dropdown and blur the input |

The currently highlighted result has a gray background. Results scroll into view as you navigate with the keyboard.

## Search highlighting

When you navigate to a page from a search result, the URL includes a `?highlight=query` parameter. On that page, Trail's highlight script:

1. Reads the `highlight` query parameter.
2. Walks all text nodes in the article content (excluding `<script>`, `<style>`, and `<code>` elements).
3. Wraps matching text in `<mark class="search-highlight">` elements.
4. Scrolls to the first match.

The highlight styling is a subtle blue underline with a light blue background, designed to be visible without obscuring the text. The highlight adapts to dark mode.

## How it differs from server-side search

Trail's search is entirely client-side. There is no server, no API, and no external search service. This means:

- **No infrastructure required.** Search works on any static host.
- **No network requests during search.** After the initial index load, all matching happens in the browser.
- **Index size scales with content.** Very large sites (thousands of pages) may produce a large `search-index.json`. The 500-character content truncation keeps this manageable for most documentation sites.
- **No typo tolerance beyond fuzzy matching.** Fuse.js provides fuzzy matching (character transpositions, insertions, deletions) but not synonym expansion or stemming.

---
title: CLI Reference
type: reference
order: 10
description: Complete reference for the trail command-line interface, covering the build and serve commands with all flags.
---

Trail is invoked as a single binary with subcommands. There are two commands: `build` and `serve`.

## Usage

```
trail <command> [flags]
```

Running `trail` with no arguments, or with `help`, `--help`, or `-h`, prints the usage summary.

## trail build

Build the static site from the project directory.

```
trail build [--dir <path>] [--output <path>]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` (current directory) | Path to the site root directory. This directory must contain `trail.toml`. |
| `--output` | `_site` | Path to the output directory. Trail deletes this directory and recreates it on every build. |

### Behavior

1. Reads `trail.toml` from the `--dir` directory.
2. Loads all content from `content/` (or `content/product-slug/` in multi-product mode).
3. Loads all pathway definitions from `pathways/`.
4. Renders every page from Markdown to HTML.
5. Applies post-processing transforms (admonitions, tab groups, mermaid, inter-page links, table wrapping, anchor links).
6. Generates index pages for the homepage, each category, and each product.
7. Generates the pathways listing page.
8. Generates the 404 page.
9. Generates the print-all page at `/print/`.
10. Generates `pathways.json` (pathway manifest for client-side navigation).
11. Generates `search-index.json` (search index for Fuse.js).
12. Generates `sitemap.xml` and `robots.txt`.
13. Copies the `static/` directory to the output root.
14. Writes JavaScript and CSS assets to `/assets/`.
15. Validates internal links and prints warnings for broken ones.
16. Prints a build summary.

### Output

```
Built 42 pages in 8 categories with 3 pathways -> _site
```

If there are broken internal links, warnings are printed before the summary:

```
Warning: 2 broken internal link(s):
  guides/install/index.html -> /reference/missing-page/
  overview/index.html -> /guides/nonexistent/
```

### Examples

Build from the current directory:

```
trail build
```

Build from a specific directory:

```
trail build --dir /path/to/my-docs
```

Build to a custom output directory:

```
trail build --output dist
```

## trail serve

Start a local development server with live reload.

```
trail serve [--dir <path>] [--port <n>]
```

### Flags

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` (current directory) | Path to the site root directory. |
| `--output` | `_site` | Path to the output directory. |
| `--port` | `3000` | Port for the HTTP server. |

### Behavior

1. Performs an initial full build (same as `trail build`).
2. Writes the live reload script to `/assets/livereload.js`.
3. Starts an HTTP server on the specified port.
4. Opens an SSE endpoint at `/__reload` for live reload connections.
5. Polls for file changes every 500 milliseconds.
6. On any change, rebuilds the site and notifies all connected browsers.

### Output

```
Serving on http://localhost:3000 (live reload enabled)
```

On each rebuild:

```
Rebuilt.
```

### Examples

Serve from the current directory:

```
trail serve
```

Serve on a different port:

```
trail serve --port 8080
```

Serve from a specific directory:

```
trail serve --dir ./docs --port 4000
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Error (configuration error, build failure, or port already in use) |

Errors are printed to stderr with the prefix `trail:`.

---
title: Dev Server
type: concept
description: Trail's dev server watches for file changes and reloads the browser automatically via Server-Sent Events.
---

The `trail serve` command starts a local development server with live reload. It builds the site, serves it over HTTP, and watches for changes.

## Starting the server

```
trail serve
```

The server starts on port 3000 by default:

```
Serving on http://localhost:3000 (live reload enabled)
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` (current directory) | Site root directory containing `trail.toml`. |
| `--port` | `3000` | Port for the HTTP server. |
| `--output` | `_site` | Output directory for the built site. |

Example with custom port and directory:

```
trail serve --dir ./docs --port 8080
```

## Live reload

The dev server watches for file changes using a polling mechanism. Every 500 milliseconds, it checks the most recent modification time of all files in the project directory (excluding `_site/` and hidden directories).

When a change is detected:

1. The site is rebuilt in full.
2. A live reload JavaScript file is written to the output.
3. All connected browsers are notified via Server-Sent Events (SSE).
4. The browser reloads the page.

### How SSE reload works

The dev server exposes an SSE endpoint at `/__reload`. The live reload script (`/assets/livereload.js`) opens an EventSource connection to this endpoint. When the server sends a `data: reload` event, the script calls `window.location.reload()`.

If the SSE connection drops (e.g., the server restarts), the script closes the connection and retries with a page reload after 1 second.

The live reload script is only injected during `trail serve`. It is not present in `trail build` output.

## 404 handling

The dev server provides proper 404 handling during development. When a request does not match any file or directory in the output:

1. The server returns HTTP status 404.
2. The body is the contents of `404.html` from the output directory.

This lets you see the same 404 page during development that readers see in production.

## File serving

The dev server serves the output directory as static files. It handles both direct file paths and directory-style URLs:

- `/assets/search.js` serves the file directly.
- `/guides/install` checks for `/guides/install/index.html` and serves it.
- `/guides/install/` serves `/guides/install/index.html`.

## What triggers a rebuild

Any file change in the project directory triggers a full rebuild. This includes:

- Content files (`content/**/*.md`)
- Configuration (`trail.toml`)
- Pathway definitions (`pathways/**/*.toml`)
- Static files (`static/**/*`)

The rebuild is complete -- Trail regenerates all pages, search index, sitemap, and assets. For most documentation sites, this takes under a second.

## Comparison to trail build

| Aspect | `trail build` | `trail serve` |
|---|---|---|
| Builds the site | Yes | Yes (initial + on change) |
| Starts HTTP server | No | Yes |
| Live reload | No | Yes |
| Live reload script | Not included | Injected |
| Intended for | Production builds, CI | Local development |

---
title: The Manifest and the Catalogue
description: A directory whose name is its id, a manifest.toml, and a catalogue that is nothing but the directory listing.
---

Applications install under `/usr/share/atrium/apps/<id>/`, one
directory per application, shipped by ordinary packages. Nothing runs
at install and nothing registers: presence is the catalogue. The
session host reads the directory on every request, so an installed
package's app appears on the next Toolbox load.

The id is reverse-DNS (`org.peios.terminal`), lowercase letters,
digits, hyphens and dots, and **the directory name is the id** — a
manifest whose `id` disagrees with its directory is a broken package
and is skipped, with a line on the session's log.

`manifest.toml`:

| Field | Meaning |
|---|---|
| `id` | The application id; equal to the directory name |
| `name` | Display name |
| `description` | One line, shown on the tile |
| `category` | Grouping label for the launcher; optional |
| `icon` | A file in the directory, served as the icon; optional |
| `glyph`, `color` | A built-in stroked glyph name and chip colour, used when no icon ships |
| `entry` | The document the window loads; default `index.html` |
| `[capabilities]` | What the app may ask the session for (§5.5) |

The session host serves `/apps/<id>/<file>` from the application's
directory, rejecting any path that could escape it, and serves the
catalogue as JSON at `/api/apps` with each entry's `entry` and `icon`
already resolved to URLs.

Two stylesheets are served to every application from the shell's own
assets: `/shell/tokens.css`, the design system's variables plus body
ground defaults — an application that links it and styles with
`var(--c-*)` matches the shell in both themes with no colours of its
own — and the SDK at `/shell/sdk.js`.

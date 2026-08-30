---
title: Message Reference
description: The mirror websocket and the frame bus, message by message.
---

## The mirror websocket (`/ws`)

One JSON object per text frame. Shell → session:

| Message | Fields | Effect |
|---|---|---|
| `launch` | `app`, `new?` | Open (or focus) an application |
| `focus` | `id` | Focus a window, restoring it if minimised |
| `minimize` | `id` | Minimise a window |
| `close` | `id` | Close a window |
| `set-title` | `id`, `title` | Rename a window (relayed from its app) |
| `app` | `win`, `req`, `body` | An application request, shell-stamped |

Session → shell:

| Message | Fields | Audience |
|---|---|---|
| `snapshot` | `windows`, `focus`, `keymap` | The connecting tab |
| `window.opened` | `window` | Every tab |
| `window.closed` | `id` | Every tab |
| `window.minimized` / `window.restored` | `id` | Every tab |
| `window.titled` | `id`, `title` | Every tab |
| `focus` | `id` (nullable) | Every tab |
| `app.reply` | `win`, `req`, `body` | The asking tab |
| `app.stream` | `win`, `req`, `body` | The asking tab |
| `error` | `message` | The asking tab |

## The frame bus (postMessage)

App → shell: `hello {v}` · `set-title {title}` · `close` ·
`request {req, body}` (`req` 0 marks fire-and-forget: `pty-input`,
`pty-resize`) · `chord {chord}` (a captured reserved chord).

Shell → app: `ready {window, theme, user, reserved}` ·
`theme {theme}` · `reply {req, body | error}` · `stream {req, body}`.

## Application request kinds

| Kind | Capability | Reply |
|---|---|---|
| `system-info` | — | Hostname, kernel, uptime, user, logon session, host pid, Atrium version |
| `exec` | `exec` allowlist | Streamed output, then `{exit_code, exit_signal, truncated}` |
| `pty-open` | `pty` | Streamed output; reply on shell exit |
| `pty-input`, `pty-resize` | `pty` | None (fire-and-forget) |

---
title: The SDK
description: One ES module an application imports — the handshake that reveals the frame, requests and streams, shortcuts, title and theme.
---

`/shell/sdk.js` is a dependency-free ES module. Importing it sends
`hello` to the shell; everything else hangs off the exported `atrium`
object.

**The handshake.** A window's frame is created hidden. When the SDK's
`hello` arrives, the shell answers `ready` with the window id, the
current theme, the user (username and display name) and the reserved
chord list, and reveals the frame; `atrium.ready()` resolves with that
context. A page that never sends `hello` is revealed by a 1.2-second
grace instead. The SDK sets `data-theme` on the document root at
`ready` and keeps it current, which is what drives `tokens.css`
variables; `atrium.on('theme', fn)` hears changes.

**Requests.** `atrium.request(body)` sends one JSON object to the
session and resolves with the reply. Kinds that stream — `exec` —
deliver interim parts to an optional second argument before the final
reply. Convenience wrappers:

- `atrium.exec(cmd, onOutput)` — run an allowlisted program (§5.5);
  `onOutput(text, stream)` receives stdout and stderr as they happen;
  resolves with `{ exit_code, exit_signal, truncated }`.
- `atrium.pty({ cols, rows, onData })` — open a terminal (§5.5);
  returns `{ write, resize, done }`.

**Window verbs.** `atrium.setTitle(s)` renames the window — session
state, visible in every tab's bar and sidebar. `atrium.close()` asks
the shell to close this window.

**Shortcuts.** `atrium.shortcuts.on(chord, fn)` registers an
application-local chord, active while the window has focus. Reserved
chords never fire here; they are captured first and forwarded to the
shell (§4.3).

**The declarative layer.** For wrapper apps, the SDK wires clicks on
any element carrying `data-atrium-exec`:

```html
<button data-atrium-exec="peipkg list" data-atrium-target="#out">
  Installed packages
</button>
<pre id="out"></pre>
```

Output streams into the target as text; the exit status lands on the
target as a `data-exit` attribute; the trigger is disabled while the
command runs. The command string is split on whitespace with no
quoting — an invocation that needs quoting has outgrown the attribute
and uses `atrium.exec`.

---
title: Configuration
type: reference
description: The window is configured in Lua, with an init.lua that binds keys, listens for key presses, and splits, focuses and closes panes. Where the files go, how a key travels through handlers and bindings, the API so far, and what happens when the config goes wrong.
related:
  - clackatoo/reference/window
  - clackatoo/reference/cli
---

The window's behaviour is configured in code: an `init.lua`, as Neovim's is, written in [Luau](https://luau.org), a fast dialect of Lua with optional types and a sandbox. Without one, the window works as it always does. Settings needed before the window starts, such as the font, stay in [`client.toml`](~clackatoo/reference/window#settings).

```lua
-- ~/.config/clackatoo/client/init.lua

-- tmux's split keys, as well as clackatoo's own.
client.keys.map("niv", '<C-b>"', function(ev) ev.pane:split("below") end)
client.keys.map("niv", "<C-b>%", function(ev) ev.pane:split("right") end)

-- Closing a pane takes :close, not a key.
client.keys.unmap("niv", "<C-b>x")

-- x in normal mode closes a chat, and does what it always did elsewhere.
client.keys.map("n", "x", function(ev)
  if ev.pane.kind ~= "chat" then return ev:propagate() end
  ev.pane:close()
end)
```

## Where it goes

```
~/.config/clackatoo/        or $XDG_CONFIG_HOME/clackatoo/
  client/init.lua           the window's config
  client/lua/               modules for it to require
  lua/                      modules shared with the daemon's config, once it has one
  client.toml               the window's settings
```

`require("theme")` loads `theme.lua` from `client/lua/`, or else `lua/`, or `theme/init.lua` from either. A dot in a name is a directory: `require("keys.tmux")` is `keys/tmux.lua`. Each module runs once, and later requires get what it returned.

The config runs once for the client, the process that opens windows, so its bindings apply in every window. It runs on a thread of its own, alongside the window starting up, and a typical config takes under a millisecond. The window never waits for it to show itself: keys pressed before it has run do what they do without it.

`:reload` runs the config again, from the start. Everything the old config bound or listened for goes, and the window's own keys come back first.

## How a key travels

Each key you press goes through, in order:

1. **Keypress handlers**, added with `on("keypress", …)`, in the order they were added. A handler on a pane only hears keys pressed in that pane.
2. **Bindings**, the window's own and those made with `client.keys.map`.
3. **The pane**: the program in a terminal, the box in a chat, or the pane's normal mode.

A handler lets the key go on unless it calls `ev:stop()`, which ends its journey there. A binding stops its keys unless it calls `ev:propagate()`, which lets them go on to the pane, as if they weren't bound. If the binding took several keys, such as `<C-b>x`, they all go on, in order.

Whether a key goes on is decided when the handler finishes, or first waits for something, as `pane:split` waits for the new pane. Calling `stop` or `propagate` after that is a mistake. A key waits at most 300 milliseconds for the config to decide. After that, it's as if the config had done nothing more: a binding's keys stop there, and a key a handler heard goes on.

## Keys

`client.keys.map(modes, keys, function)` binds keys in one or more modes, replacing what they were bound to. `client.keys.unmap(modes, keys)` takes a binding away, the window's own included.

**Modes** are written as letters, together: `"niv"` is all three of normal, insert and visual. `c` is typing into a pane's prompt, such as a search.

**Keys** are written as in Vim. A character is itself, and `<…>` holds a key with modifiers or a named key:

| Written | Is |
|---|---|
| `<C-b>`, `<A-h>` | Ctrl+B, Alt+H |
| `<C-O>`, `<C-S-o>` | Ctrl+Shift+O. Shift is part of a letter: `<C-o>` is Ctrl+O. |
| `<S-Tab>` | Shift with a named key |
| `<Esc>`, `<CR>`, `<Tab>`, `<BS>`, `<Del>`, `<Insert>`, `<Space>` | Named keys. `<Enter>` and `<Return>` are `<CR>`. |
| `<Up>`, `<Down>`, `<Left>`, `<Right>`, `<Home>`, `<End>`, `<PageUp>`, `<PageDown>`, `<F1>`–`<F12>` | More named keys |
| `<lt>` | `<` |

Several keys in a row, such as `<C-b>"`, make a sequence. A key that starts one waits for the rest as long as it takes, as tmux's prefix does, and a key that matches nothing drops the keys typed so far. So a binding whose keys start a longer binding's, such as `<C-b>` beside `<C-b>x`, can't be reached.

## Events and handles

`client.on("keypress", function)` listens for keys anywhere. Windows, tabs and panes have `:on` too, to listen only there. Each returns a subscription, whose `:off()` stops it. A pane's or tab's handlers go when it closes.

A handler gets the event, `ev`:

| Field | Is |
|---|---|
| `ev.key` | The key, as a binding writes it, such as `<C-b>` or `q` |
| `ev.keys` | For a binding, all of its keys |
| `ev.text` | The text the key types, if any |
| `ev.mode` | The mode's letter |
| `ev.pane`, `ev.window` | Where it was pressed |

Windows, workspaces, tabs and panes are handles: values that stand for one of them, whose fields are read as they are at the time. Reading a pane that has closed is a mistake. Two handles to the same pane are equal.

| | Fields | Methods |
|---|---|---|
| `client` | `windows`, `focused` (the focused pane) | `on`, `keys.map`, `keys.unmap` |
| A window | `workspace`, `tab`, `pane` | `on` |
| A workspace | `name`, `tabs` | `on` |
| A tab | `name`, `panes`, `focused`, `workspace` | `on` |
| A pane | `kind` (`"terminal"` or `"chat"`), `title`, `tab` | `on`, `split`, `close`, `focus` |

`pane:split(side)` puts a new pane on that side, `"right"`, `"left"`, `"below"` or `"above"`, of the same kind, or another with `{ kind = "chat" }`. It waits for the daemon to make it, then focuses it, as Ctrl+B `|` does, and returns it:

```lua
client.keys.map("n", "<C-b>t", function(ev)
  local below = ev.pane:split("below")
  below:split("right")
end)
```

While it waits, the window carries on, and so does the key. Each handler and binding runs in a coroutine, a function that can pause partway and carry on later, so waiting holds up nothing else.

Nothing is shown while `init.lua` first runs, so `client.focused` is nil then: handles are for handlers.

## When it goes wrong

A mistake, such as a key that doesn't exist, a mode that isn't one, or a pane that has closed, is shown in the bottom bar, with the file and line, until the next key, and printed on stderr in full. A mistake in `init.lua` itself stops it there, as an error in any Lua program does: what it bound before that line stays bound.

A handler or binding that runs for more than a quarter of a second at a time, as a loop that never ends would, is stopped there, and its key is decided as if it had done nothing more.

`print` writes to stderr.

## Not yet

- The daemon has no config yet.
- `init.lua` isn't run again when it changes: use `:reload`.
- Bindings made in Lua don't show in Ctrl+B's list in the bottom bar.
- Keypresses are the only event.
- There are no type definitions for editors to complete the API with.

---
title: Keybinds
description: Three tiers of chord ownership, a session-owned table, and cooperative capture inside application frames.
---

Keyboard chords have three owners, and the boundaries are physical
rather than chosen:

1. **The browser and OS** own what they own — `Ctrl+W`, `Ctrl+T`,
   `Alt+Tab`, `F11` on most browsers — and a web page never sees some
   of them. Atrium's defaults avoid the common ones.
2. **The shell** owns the reserved chords: global desktop actions that
   work everywhere, including while an application frame has focus.
3. **The focused application** owns everything else.

The chord table is session state, shipped in the snapshot as
`keymap`: a list of `{ chord, action }`. Chords are written as sorted
modifiers plus a key — `Ctrl+Alt+T`, key from the keyboard event's
`key` value, single characters uppercased. Actions are strings; every
action today is a shell action, and the string form is what leaves
room for application-owned globals later without a schema change.

| Chord | Action |
|---|---|
| `Ctrl+K` | `command-bar` |
| `Alt+T` | `toolbox` |
| `Alt+W` | `close-window` |
| `Alt+M` | `minimize-window` |
| `Alt+1`…`Alt+9` | `focus-window-1`…`9` |
| ``Ctrl+` `` | `cycle-window` |

In the shell's own document, a capture-phase listener matches the
table and runs the action. Inside an application frame, the shell
cannot hear keys at all — so the SDK carries the shell's half inward:
it receives the reserved chord list with `ready`, captures those
chords at its own capture phase, prevents the default, and posts the
chord back to the shell, which runs the action. Everything else
passes to the application untouched.

The arrangement is cooperative. A frame that does not load the SDK
swallows global chords while focused — the documented cost of not
integrating — and a hostile frame could at worst do the same, since
the shell acts only on chords present in its own table.

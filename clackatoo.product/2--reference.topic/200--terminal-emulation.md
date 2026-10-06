---
title: Terminal emulation
type: reference
description: The terminal clackatoo emulates. What programs find in their environment, which escape sequences and modes it supports, which queries it answers, and what it ignores so far.
related:
  - clackatoo/reference/cli
  - clackatoo/getting-started/what-is-clackatoo
---

clackatoo emulates enough of xterm for shells, ncurses programs such as htop, and vim, under `TERM=xterm-256color`. Sequences it doesn't support are ignored, as xterm ignores ones it doesn't know.

## The environment

A program started in a clackatoo terminal gets the daemon's environment, with these changes:

| Variable | Value |
|---|---|
| `TERM` | `xterm-256color` |
| `COLORTERM` | `truecolor` |
| `TERM_PROGRAM` | `clackatoo` |
| `TERM_PROGRAM_VERSION` | The clackatoo version. |

Variables describing whatever terminal the daemon was started in are removed, so programs don't think they're inside it. These include `TMUX`, `TMUX_PANE`, `STY`, `VTE_VERSION`, `KITTY_WINDOW_ID`, `WEZTERM_PANE`, `ALACRITTY_WINDOW_ID`, `ITERM_SESSION_ID`, `WT_SESSION`, `COLUMNS` and `LINES`.

The program runs in its own session, with the terminal as its controlling terminal, so job control and Ctrl-C work as usual.

## Screen behaviour

- **Scrollback**: the primary screen keeps the last 10,000 lines that scroll off its top. Lines only enter scrollback when the whole screen scrolls. Scrolling inside a region an app has narrowed (as vim does) discards them.
- **Alternate screen**: full-screen programs switch to a second screen with no scrollback. Leaving it restores the primary screen and cursor exactly.
- **Wrapping**: printing in the last column leaves the cursor there, and the line wraps only when the next character arrives.
- **Background colour erase**: clearing part of the screen fills it with the current background colour.
- **Wide characters** take two columns. A wide character that doesn't fit at the end of a line wraps to the next one.
- **Combining characters** (accents, variation selectors) join the character before them. So do characters after a zero-width joiner, so emoji sequences such as 👩‍💻 stay one character.

## Supported sequences

| Kind | Supported |
|---|---|
| Control characters | BS, HT, LF, VT, FF, CR, SO, SI. BEL is accepted and ignored. |
| `ESC` | `7` `8` (save/restore cursor), `D` (index), `E` (next line), `H` (set tab stop), `M` (reverse index), `c` (full reset), `#8` (screen alignment test), `(` and `)` with `B` (ASCII) or `0` (DEC line drawing) |
| `CSI` cursor | `A` `B` `C` `D` `E` `F` `G` `H` `I` `Z` `` ` `` `a` `d` `e` `f`, and `s` `u` without parameters |
| `CSI` editing | `@` `J` (including `3J` to clear scrollback) `K` `L` `M` `P` `S` `T` `X` `b` (repeat) |
| `CSI` other | `g` (clear tab stops), `r` (scroll region), `m` (SGR), `!p` (soft reset) |
| ANSI modes (`CSI h`/`l`) | 4 (insert), 20 (line feed is newline) |
| DEC modes (`CSI ? h`/`l`) | 6 (origin), 7 (autowrap), 25 (show cursor), 47, 1047 and 1049 (alternate screen), 1048 (save cursor) |
| SGR | Bold, dim, italic, blink, inverse, hidden, strikethrough and their resets. Underlines: single, double (`21` or `4:2`), curly (`4:3`), dotted (`4:4`), dashed (`4:5`). 8, 16, 256 and 24-bit colours for text, background and underline (`58`), in both the `;` and `:` spellings. |
| `OSC` | 0 and 2 (window title) |

## Queries answered

| Query | Reply |
|---|---|
| `CSI c` (primary device attributes) | `CSI ? 62 ; 22 c`: a VT220 with colour |
| `CSI 5 n` (status) | `CSI 0 n` |
| `CSI 6 n` and `CSI ? 6 n` (cursor position) | `CSI <line> ; <col> R`, with `?` for the second form. Relative to the scroll region in origin mode. |
| `CSI > q` (terminal version) | `DCS > \| clackatoo <version> ST` |

## Not supported yet

The terminal can't be resized after it starts. These are ignored:

- Modes that only change how keys and the mouse are reported: cursor-key mode, keypad mode, mouse tracking, bracketed paste and focus events. A window client will need them, so they come with it.
- OSC 7 (working directory), OSC 8 (hyperlinks), OSC 52 (clipboard) and OSC 133 (shell integration).
- Secondary device attributes (`CSI > c`) and the kitty keyboard protocol.
- Left and right margins (`CSI s` with parameters).
- Variation selector 16 does not widen the character before it.

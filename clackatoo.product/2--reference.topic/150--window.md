---
title: The window
type: reference
description: clackatoo's window shows a terminal and sends it your keys. Insert mode types into the program; normal mode moves a cursor of clackatoo's own through history, to scroll, select, copy and search.
related:
  - clackatoo/getting-started/quick-start
  - clackatoo/reference/cli
  - clackatoo/reference/terminal-emulation
---

The window is a client of the daemon, like the `clackatoo` command. It shows one terminal, keeps up with it as its program prints, and sends it your keys. Closing the window closes nothing: the terminal keeps running in the daemon, and the next window shows it again.

## Opening it

```sh
clackatoo
```

With no command, `clackatoo` opens a window on your newest running terminal, or starts a terminal running your `$SHELL` if there is none. If no daemon is running, it starts one in the background first. That daemon logs to `daemon.log` in the [runtime directory](~clackatoo/reference/cli), and keeps running after the window closes.

The window sizes itself for a 100×30 terminal. Resizing the window resizes the terminal, and its program is told the new size.

| Option | Environment variable | |
|---|---|---|
| `--font <FAMILY>` | `CLACKATOO_FONT` | The font family. Default: your system's monospace font. |
| `--font-size <POINTS>` | `CLACKATOO_FONT_SIZE` | The text size. Default: 12. |

A font family is named as fontconfig knows it, as `fc-list : family` prints. Characters the font doesn't have, such as CJK text or emoji, come from fallback fonts, found the same way.

### A daemon from another build

Each build of clackatoo speaks one version of the protocol between windows and the daemon, and refuses a daemon speaking another. When the window finds a daemon from an older build, it says so and offers to replace it:

- Enter stops the old daemon and starts a new one. This closes every terminal in the old daemon, and hangs up their programs.
- Esc quits, leaving the old daemon running.

`clackatoo stop` does the same from the command line.

## Modes

The window is in one of two modes, like Vim:

- **Insert mode**, where it starts. Keys go to the program.
- **Normal mode**. Keys drive clackatoo. A yellow frame round the window, and a label in its top right corner, show that you're in it.

| Key | In | Does |
|---|---|---|
| Shift+Esc or Ctrl+\\ | insert mode | Switches to normal mode. |
| `i` | normal mode | Switches to insert mode, back at the live screen. |
| Ctrl+\\, twice | insert mode | Sends a real Ctrl+\\ to the program. |
| Ctrl+C | either | Interrupts the program. |

Plain Esc always goes to the program, since programs such as Vim and less use it.

## Typing

In insert mode, keys reach the program the way xterm sends them, which nearly every program understands:

- Text types itself. Ctrl with a letter sends its control character (Ctrl+C, Ctrl+D…). Alt sends Escape before the key.
- Enter, Backspace, Tab, Shift+Tab and Escape send their usual codes. Ctrl+Backspace deletes a word in most shells.
- Arrows, Home, End, Insert, Delete, Page Up, Page Down and F1 to F12 send escape sequences, with any modifiers held.
- When a program asks for them, arrows and the number pad send application codes, which Vim and less expect.

Ctrl+Shift+V pastes. If the program has asked for bracketed paste, the text is marked as pasted, so editors don't treat it as typing and shells don't run it line by line. Otherwise newlines are sent as Enter.

Typing while scrolled up returns the view to the live screen.

## Scrolling

The mouse wheel scrolls history in either mode. On the alternate screen, which full-screen programs use and which has no history, the wheel sends arrow keys instead, so less, Vim and htop scroll themselves.

While the view is scrolled up, the label shows how far, as `↑42`, and new output doesn't move what you're reading.

## Normal mode

Normal mode has a cursor of its own, a yellow block, which moves through the terminal's history and screen as one document. It starts where the program's cursor is, and the program's cursor is hidden until you return to insert mode.

| Keys | Move |
|---|---|
| `h` `j` `k` `l`, arrows | Left, down, up, right. Moving up and down returns to the column you started from after passing shorter lines. |
| `w` `b` `e` | To the next word's start, this or the previous word's start, this or the next word's end. Words are runs of letters, digits and `_`, or runs of other characters; both cross line ends. |
| `0` `$`, Home End | The line's first column, its last character. |
| `gg` `G` | The oldest line of history, the screen's last line. |
| `H` `M` `L` | The top, middle and bottom lines in view. |
| Ctrl+D Ctrl+U | Half a screen down or up, view and cursor together. |
| Ctrl+F Ctrl+B, Page Down Page Up | A screen down or up. |
| Ctrl+E Ctrl+Y | The view a line down or up, with the cursor kept in it. |

Moving past the top of the view scrolls into history. In normal mode the view holds still while output arrives, so the cursor stays on its text. On the alternate screen the cursor moves over the screen only.

### Selecting and copying

| Keys | Does |
|---|---|
| `v` | Selects characters, from the cursor to wherever it moves. |
| `V` | Selects whole lines. |
| `o` | Moves the other end of the selection. |
| `y`, Ctrl+Shift+C | Copies the selection to the clipboard, and returns to normal mode. |
| `yy`, `Y` | Copies the cursor's line. |
| Esc | Drops the selection. |

Any motion extends a selection, including `gg`, `G` and searches. Copied text is what the program printed: a line that wrapped only because it reached the window's edge comes out as one line, blanks at the ends of lines are left out, and there is no newline after the last line, so pasting it into a shell never runs it.

### Searching

| Keys | Does |
|---|---|
| `/` | Searches forward from the cursor. Type the text, shown in the label, then Enter. Esc cancels. |
| `?` | Searches backward. |
| `n` `N` | Searches again, the same way or the other way. |
| Esc | Clears the highlight on the last match. |

A search ignores case unless the text has a capital letter in it. It covers all of history and wraps around at either end. The cursor moves to the match, which is highlighted. If there's none, the label says `not found`.

Copying and searching both happen in the daemon, which holds all of history, so neither waits for the window to fetch the lines involved.

## The cursor

In insert mode, the cursor has the shape the program asks for: a block, an underline or a bar, which Vim and shells in vi mode switch between. If the program hasn't asked, it's a bar. In normal mode it's always clackatoo's yellow block. While the window isn't focused, either cursor is drawn as an outline.

## Drawing

The window draws with the GPU, and only when something changed: a quiet terminal costs no CPU. It redraws at most once per frame, so a flood of output costs one frame's drawing per frame.

Box-drawing characters (`─` `│` `┌` `╭` `═`…) and block elements (`█` `▄` `░`…) are drawn by clackatoo rather than taken from the font, so that borders in htop, tmux or Vim join up across lines at any size. The diagonal lines come from the font.

## Not supported yet

- Typing through an input method, for languages such as Chinese and Japanese.
- Selecting with the mouse, and mouse input for programs.
- Emoji joined with a zero-width joiner, such as 👩‍💻, show only their first emoji.
- History lines are shown at the width they were printed at. A line that wrapped in a narrower window doesn't rewrap when the window gets wider.

---
title: The window
type: reference
description: clackatoo's window shows your workspaces, their tabs and their panes of terminals, and sends your keys to the focused one. Insert mode types into the program; normal mode moves a cursor of clackatoo's own through history, and runs the window's commands.
related:
  - clackatoo/getting-started/quick-start
  - clackatoo/reference/cli
  - clackatoo/reference/remote
  - clackatoo/reference/terminal-emulation
---

The window is a client of the daemon, like the `clackatoo` command. It shows a workspace's terminals, keeps up with them as their programs print, and sends your keys to the one with the focus. Closing the window closes nothing: the terminals keep running in the daemon, and the next window shows them again, laid out as they were.

## Opening it

```sh
clackatoo
```

With no command, `clackatoo` opens a window on your [workspaces](#workspaces-tabs-and-panes): the one last used, at the tab and pane last used. If there are none, it makes one, showing your newest running terminal, such as one started with `clackatoo new`, or else a new terminal running your `$SHELL`. If no daemon is running, it starts one in the background first. Until the daemon answers, the window says it's connecting, and Esc quits. That daemon logs to `daemon.log` in the [runtime directory](~clackatoo/reference/cli), and keeps running after the window closes.

The window sizes itself so that its one pane holds 100×30 cells. Resizing the window resizes each pane's terminal to fit, and its program is told the new size. When several windows show one terminal, the terminal takes the size of whichever was last opened on it, resized or focused.

With `--remote <HOST>`, the window shows the workspaces on another machine, through ssh. See [another machine](~clackatoo/reference/remote).

| Option | Environment variable | [Setting](#settings) | |
|---|---|---|---|
| `--font <FAMILY>` | `CLACKATOO_FONT` | `font` | The font family. Default: your system's monospace font. |
| `--font-size <POINTS>` | `CLACKATOO_FONT_SIZE` | `font-size` | The text size. Default: 12. |
| `--renderer <API>` | `CLACKATOO_RENDERER` | `renderer` | The graphics API to draw with: `vulkan` (the default) or `opengl`. See [drawing](#drawing). |
| `--remote <HOST>` | | | Use the daemon on another machine. |
| `--remote-command <COMMAND>` | `CLACKATOO_REMOTE_COMMAND` | | The command that runs clackatoo there. Default: `clackatoo`. |

An option on the command line wins over its environment variable, which wins over the setting.

## The frame

The window draws its own frame, in place of the desktop's:

- **The top bar** holds your [workspaces](#workspaces-tabs-and-panes), with the one shown picked out, and a `+` after them that makes a new one. The window's buttons sit at whichever end your desktop puts them, in the same order. Drag the bar to move the window, double-click it to maximise or restore it, and right-click it for the desktop's window menu.
- **The bottom bar** holds the tabs of the workspace shown, with a `+` after them that opens a new one. On its right is a note: the [mode](#modes), how far the view is [scrolled](#scrolling), or a message, such as why a command failed.
- **The panes** sit on cards between the bars, each a little in from its edges. The focused pane's card has a blue edge, or a yellow one in normal mode.
- **The palette** opens in the middle of the window for anything typed to clackatoo itself: [commands](#the-command-line), [searches](#searching) and new names.

Drag the window's edges or corners to resize it. Interface text, such as the names in the bars, is in your desktop's interface font. On GNOME, both the font and where the buttons go come from its settings.

With the mouse:

- Click a workspace or tab to show it, and a pane to focus it.
- Click a `+` to make a workspace, or open a tab.
- Right-click a workspace or tab for **Rename** or **Close**. Rename opens the palette with the name to change. Clearing a tab's name names it after its focused pane's program again. Close closes every pane in it, hanging up their programs.

## Settings

Settings you rarely change, or change to tune how the window starts, live in `client.toml`: `$XDG_CONFIG_HOME/clackatoo/client.toml`, or `~/.config/clackatoo/client.toml`. The window reads it before anything else starts, which takes a few microseconds.

```toml
font = "JetBrains Mono"
font-size = 12
renderer = "opengl"
```

`clackatoo config` shows and changes them, keeping the rest of the file, comments included, as it was:

```sh
clackatoo config renderer opengl   # set one
clackatoo config renderer          # show one
clackatoo config --unset renderer  # back to its default
clackatoo config                   # all of them, and where the file is
```

A mistake in the file never stops the window opening. Each setting with a mistake, such as an unknown name or a value of the wrong kind, is reported on stderr and left at its default, and the rest still apply.

The settings are on this machine. With [`--remote`](~clackatoo/reference/remote), the window's settings come from the machine the window opens on.

A font family is named as fontconfig knows it, as `fc-list : family` prints. Characters the font doesn't have, such as CJK text or emoji, come from fallback fonts, found the same way.

### A daemon from another build

Each build of clackatoo speaks one version of the protocol between windows and the daemon, and refuses a daemon speaking another. When the window finds a daemon from another build, it says so, and what Enter does depends on which is older:

- **An older daemon, from protocol 11 on:** Enter upgrades it. The daemon becomes this build without stopping, so its terminals and the programs in them carry on, and the window opens on them.
- **An older daemon, from before protocol 11:** it's too old to upgrade, so Enter stops it and starts a new one. This closes every terminal in the old daemon, and hangs up their programs.
- **A daemon newer than the window:** the window says to open a window from the newer build instead. It never offers to replace a newer daemon.

Esc quits, leaving the daemon running. [`clackatoo upgrade`](~clackatoo/reference/cli#upgrade) and `clackatoo stop` do the same from the command line.

### Losing the daemon

If the connection to the daemon is lost, because the daemon stopped or, [on another machine](~clackatoo/reference/remote), the network went, the window says so and why, in place of the terminal:

- Enter reconnects, starting a daemon if none is running. If the workspace shown is still there, the window returns to it, with each pane as it was, in the same mode and scrolled to the same place.
- Esc quits.

When the daemon [upgrades](~clackatoo/reference/cli#upgrade), every connection to it drops for a moment. A window whose daemon on this machine is still there afterwards reconnects by itself, without asking.

## Modes

The window is in one of two modes, like Vim:

- **Insert mode**, where it starts. Keys go to the program.
- **Normal mode**. Keys drive clackatoo. The pane's card has a yellow edge, and the bottom bar's note says `NORMAL`.

Each pane has its own mode.

| Key | In | Does |
|---|---|---|
| Ctrl+; | insert mode | Switches to normal mode. |
| Shift+Esc or Ctrl+\\ | insert mode | Also switch to normal mode. |
| `i` | normal mode | Switches to insert mode, back at the live screen. |
| Ctrl+\\, twice | insert mode | Sends a real Ctrl+\\ to the program. |
| Ctrl+C | either | Interrupts the program. |

Plain Esc always goes to the program, since programs such as Vim and less use it. Ctrl+; costs programs nothing: a terminal has no code to send them for it, so none can be listening for it. It's found by where the key is, so on layouts where `;` takes Shift, such as German, it's Ctrl and the key to the right of L.

## Workspaces, tabs and panes

The window shows your work at three levels:

- **Workspaces**, one for each piece of distinct work, such as a project. Their names run along the [top bar](#the-frame). Often there's just one.
- **Tabs**, inside a workspace. They run along the bottom bar, numbered, and named after the title of their focused pane's program, unless you've named them.
- **Panes**, which a tab is split into, side by side or stacked. Each shows a terminal. Panes in a split share its space equally.

The daemon keeps all of them, as it keeps terminals. Closing the window closes nothing, and the next window opens on the workspace, tab and pane last used. Each window shows one workspace, so two windows can show two workspaces, or two tabs of one.

A pane closes when its program exits, as in other terminals. A tab closes with its last pane, and a workspace with its last tab. When the last workspace closes, so does the window.

### The command line

In normal mode, `:` opens a command line, in the palette in the middle of the window. Enter runs the command. Esc, or Backspace past the colon, closes it.

| Command | Does |
|---|---|
| `:Terminal` | Opens a terminal in a new tab. |
| `:\|Terminal` | Splits the focused pane, with a new terminal to its right. |
| `:\|<Terminal` | The same, to its left. |
| `:-Terminal` | The same, below it. |
| `:-^Terminal` | The same, above it. |
| `:1`, `:2`… | Moves to that tab of the workspace shown. |
| `:workspace NAME`, `:ws NAME` | Switches to the workspace called NAME, making it if there's none. Without a name, makes a new workspace, named with the lowest number no workspace has. |
| `:rename NAME` | Renames the workspace shown. |
| `:close`, `:q` | Closes the focused pane, hanging up its program. |

The first character of a split says which way the divider runs, `|` upright or `-` flat, and `<` or `^` after it puts the new pane first. A mark alone opens a terminal, so `:|` is `:|Terminal`. Capitalised words name kinds of pane, of which terminals are the only one so far. Lowercase words are the window's own commands, and numbers are tabs.

A new terminal starts in the directory that the pane it splits is in. A new tab's terminal starts in the directory of the workspace's focused pane.

Workspace names are unique, and can't contain `@`, which will name workspaces on other machines. If a command fails, such as renaming a workspace to a name another has, the bottom bar says why until the next key.

### Moving around

In normal mode, Ctrl+H, Ctrl+J, Ctrl+K and Ctrl+L move to the pane to the left, below, above or right. Tabs are `:1`, `:2` and so on, and workspaces `:ws NAME`.

You stay in normal mode as you move: the pane you arrive at, including a pane a command just opened, is in normal mode too, and `i` starts typing into it. The pane you left keeps its mode and its place in history.

## Typing

In insert mode, keys reach the program the way xterm sends them, which nearly every program understands:

- Text types itself. Ctrl with a letter sends its control character (Ctrl+C, Ctrl+D…). Alt sends Escape before the key.
- Enter, Backspace, Tab, Shift+Tab and Escape send their usual codes. Ctrl+Backspace deletes a word in most shells.
- Arrows, Home, End, Insert, Delete, Page Up, Page Down and F1 to F12 send escape sequences, with any modifiers held.
- When a program asks for them, arrows and the number pad send application codes, which Vim and less expect.

Ctrl+Shift+V pastes, and Ctrl+Shift+C copies text [selected with the mouse](#the-mouse); neither reaches the program. If the program has asked for bracketed paste, the text is marked as pasted, so editors don't treat it as typing and shells don't run it line by line. Otherwise newlines are sent as Enter.

Typing while scrolled up returns the view to the live screen.

## Scrolling

The mouse wheel scrolls history in either mode, in the pane under the pointer. On the alternate screen, which full-screen programs use and which has no history, the wheel sends arrow keys instead, so less, Vim and htop scroll themselves. A program that takes [the mouse](#the-mouse) gets the wheel itself.

While the view is scrolled up, the bottom bar's note shows how far, as `↑42`, and new output doesn't move what you're reading.

## The mouse

Clicking a pane focuses it. What else the mouse does depends on the program in the pane.

**Selecting.** Usually the mouse selects text:

- Dragging selects characters. Dragging past the top or bottom of the pane scrolls it.
- A double click selects a word. Paths and URLs count as one word, so `~/src/main.rs` comes whole.
- A triple click selects whole lines.

Letting go copies the selection to the primary selection, and a middle click pastes it, as elsewhere on Linux. Ctrl+Shift+C, or `y` in normal mode, copies it to the clipboard. The selection stays highlighted until the next key or click. In normal mode, a click also moves the cursor there.

**Programs that take the mouse.** Programs such as Neovim, htop and less can ask for clicks, drags and the wheel, and get them while their pane is in insert mode on the live screen. The pointer is then an arrow rather than a text cursor. Hold Shift to select text anyway. A drag stays with the pane it started in, even when the pointer leaves it.

Programs that ask are also told when their pane gains or loses the focus, which Neovim uses to reload files changed meanwhile.

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
| `/` | Searches forward from the cursor. Type the text, shown in the palette, then Enter. Esc cancels. |
| `?` | Searches backward. |
| `n` `N` | Searches again, the same way or the other way. |
| Esc | Clears the highlight on the last match. |

A search ignores case unless the text has a capital letter in it. It covers all of history and wraps around at either end. The cursor moves to the match, which is highlighted. If there's none, the bottom bar says `not found`.

Copying and searching both happen in the daemon, which holds all of history, so neither waits for the window to fetch the lines involved.

## The cursor

In insert mode, the cursor has the shape the program asks for: a block, an underline or a bar, which Vim and shells in vi mode switch between. If the program hasn't asked, it's a bar. In normal mode it's always clackatoo's yellow block. In panes without the focus, and while the window isn't focused, either cursor is drawn as an outline.

## Drawing

The window draws with the GPU, and only when something changed: a quiet terminal costs no CPU. It redraws at most once per frame, so a flood of output costs one frame's drawing per frame.

On a machine with two GPUs, the window uses the one the system lists first, which is the one driving the screen: on a desktop, usually the graphics card the monitors are plugged into, and on a laptop, the integrated GPU. Frames drawn on the other GPU may never reach the screen. To choose differently, set `WGPU_POWER_PREF` to `high` for the faster GPU, or `low` for the one that uses less power.

The window draws with Vulkan, or with OpenGL where Vulkan can't draw. On some laptops with two GPUs, OpenGL opens a window much sooner: to choose between them, Vulkan asks both about themselves, and that can take more than a second, while OpenGL can use the screen's GPU without asking the other. When setting up the GPU takes over half a second, the window says so on stderr, and suggests trying OpenGL:

```sh
clackatoo config renderer opengl
```

If the API chosen can't draw, the window uses the other.

Box-drawing characters (`─` `│` `┌` `╭` `═`…) and block elements (`█` `▄` `░`…) are drawn by clackatoo rather than taken from the font, so that borders in htop, tmux or Vim join up across lines at any size. The diagonal lines come from the font.

## Not supported yet

- Resizing or moving panes. Every split shares its space equally.
- Panes from other machines, as `:Terminal@host` will open. Today the window says this isn't built yet.
- Typing through an input method, for languages such as Chinese and Japanese.
- Emoji joined with a zero-width joiner, such as 👩‍💻, show only their first emoji.
- History lines are shown at the width they were printed at. A line that wrapped in a narrower window doesn't rewrap when the window gets wider.

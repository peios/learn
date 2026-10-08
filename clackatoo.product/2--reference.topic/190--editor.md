---
title: Editing files
type: reference
description: An editor pane edits a file with Vim's keys. The daemon keeps the file's text and its undo history, so every window edits the same text, agents' edits and yours meet, and nothing is lost when the window closes or the daemon upgrades. How to open and write files, the keys, and what doesn't work yet.
related:
  - clackatoo/reference/window
  - clackatoo/reference/cli
  - clackatoo/reference/config
---

An editor pane edits one file, with Vim's keys. Its text lives in the daemon, in a buffer, as a terminal's screen does, and each window showing it keeps a copy that it changes as you type, so a key never waits for the daemon.

```
:e src/main.rs          edit a file in a new tab
:|Editor src/main.rs    the same, beside the focused pane
:w                      write it
:q                      close the pane
```

## Opening a file

| Command | Does |
|---|---|
| `:e PATH`, `:edit PATH`, `:Editor PATH` | Opens the file in a new tab. |
| `:\|Editor PATH`, `:\|<Editor PATH`, `:-Editor PATH`, `:-^Editor PATH` | Opens it beside the focused pane: right, left, below or above, as the [split marks](~clackatoo/reference/window#the-command-line) do for terminals. |
| `clackatoo edit PATH` | From a shell: opens it in a new tab of the workspace last used. See [the CLI](~clackatoo/reference/cli#edit). |

A relative path is from the focused pane's directory: for a terminal, the directory of the program in front, as for a new terminal; for an editor, the directory its file was opened from. `~/` is your home directory.

A file that's already open is shown again, not read again: two panes on one file are two views of one buffer, each with its own cursor. A file that doesn't exist yet opens empty, and is made when it's first written. A directory, or a file that isn't UTF-8 text, can't be opened, and the bottom bar says so.

## Buffers

The daemon keeps each buffer, as it keeps terminals:

- **Every window edits the same text.** Edits made in one window, or by anyone else, show in the others, and move their cursors with the text around them.
- **Edits made at once meet.** If an agent edits a file while you type in it, both edits are kept, and every copy ends up with the same text. The daemon puts edits in order, and brings each one up to date past those made since, by operational transformation, as Google Docs does.
- **Undo undoes your edits, not anyone else's.** `u` takes back your last change, from whichever window you made it in, and leaves an agent's edits made since in place.
- **Nothing is lost when the window closes, or the daemon [upgrades](~clackatoo/reference/cli#upgrade).** Buffers come through an upgrade with their undo history.

Each command in normal mode is one undo step, as is each go of insert mode, with the command that started it, such as `cw`.

A buffer closes with its last pane, unless it has changes that aren't written. `:q` won't close that pane, and `:q!` throws the changes away. A pane closed another way, such as with Ctrl+B `x` or by closing its tab, keeps the buffer's changes, unseen: opening the file again shows them.

## Writing

| Command | Does |
|---|---|
| `:w`, `:write` | Writes the file. |
| `:w!` | Writes it even if it's changed on disk since it was read or last written. |
| `:wq`, `:x` | Writes it, then closes the pane. `:wq!` writes it even if it's changed. |
| `:q`, `:quit` | Closes the pane, unless it's the last showing a file with changes not written. |
| `:q!` | Closes the pane, throwing away the file's changes not written. |
| `:e!` | Throws away the changes not written, reading the file again. That's an edit like any other: `u` brings the changes back. |

Writing writes a new file beside the old one, with its permissions, then renames it over the old one, so the file is never half written. If something else has changed the file since it was read or last written, `:w` refuses, so as not to write over the change; `:w!` writes over it. The bottom bar shows `[+]` after the file's name while it has changes that aren't written.

## Keys

An editor starts in normal mode. The bottom bar shows the mode, the file's name, and the cursor's line and column.

### Moving

| Keys | Moves to |
|---|---|
| `h` `j` `k` `l`, the arrows | The next character or line. A count moves that many. |
| `w` `b` `e` | The start of the next word, the start of this one or the one before, the end of this one or the next. |
| `W` `B` `E` | The same, for anything between blanks. |
| `0` `^` `$` | The line's start, its first character that isn't blank, its last character. |
| `gg` `G` | The first line, the last. `12G` is line 12. |
| `f` `t` `F` `T` and a character | The next one on the line, or the character before it with `t`; back with `F` and `T`. `;` does it again, and `,` back. |
| `/` `?` | Searches forward or back. `n` and `N` find the next and previous match, going round the file's ends. Case is ignored unless the search has a capital letter. |
| Ctrl+D, Ctrl+U | Half a page down or up. |
| Ctrl+F, Page Down, Page Up | A page down, or up with Page Up. |
| `zt` `zz` `zb` | Scrolls the cursor's line to the top, middle or bottom. |

### Changing

| Keys | Does |
|---|---|
| `i` `a` `I` `A` | Insert mode before or after the cursor, at the line's first character that isn't blank, at its end. |
| `o` `O` | Insert mode on a new line below or above, indented as the cursor's line is. |
| `d`, `c`, `y` and a motion | Deletes, changes or copies what the motion moves over: `dw`, `c$`, `y2j`. |
| `d`, `c`, `y` and an object | The same, for a [text object](~clackatoo/reference/window#text-objects): `diw`, `ci"`, `ya(`. |
| `dd` `cc` `yy` | Whole lines: the cursor's, and with a count, those after it. |
| `x` `X` | Deletes the character under the cursor, or before it. |
| `D` `C` `Y` | Deletes or changes to the line's end, or copies the line. |
| `s` `S` | Changes the character under the cursor, or the line. |
| `r` and a character | Replaces the character under the cursor with it. |
| `J` | Joins the next line onto the cursor's, with a space. |
| `p` `P` | Puts what was last deleted or copied after the cursor, or before. Lines go on the line below or above. |
| `u` Ctrl+R | Undoes your last change, or redoes the last undone. |
| `.` | Makes the last change again, with what was typed in insert mode after it. A count makes it that many times. |
| `v` `V` | Visual mode, by characters or whole lines. `d`, `x`, `c`, `s` and `y` act on what's selected, `o` goes to its other end, and `i` or `a` and an object selects the object. |

`cw` changes to the end of the word, not up to the next word, as in Vim.

What `y` copies goes on the clipboard too. What `d` and `c` delete only goes where `p` puts from, so deleting doesn't lose what you copied from somewhere else.

### Insert mode

Keys type into the file. Esc, or Ctrl+; as in a terminal, goes back to normal mode.

| Keys | Does |
|---|---|
| Enter | A new line, indented as the line before. |
| Tab | Indents to the next multiple of 4 columns, with spaces, or with a tab on a line indented with tabs. |
| Backspace, Ctrl+H | Deletes the character before the cursor, joining the line to the one before at its start. |
| Delete | Deletes the character under the cursor. |
| Ctrl+W | Deletes the word before the cursor. |
| Ctrl+U | Deletes back to the end of the line's indent, or from there, to the line's start. |
| The arrows, Home, End | Move, and start a new undo step. |

A count before `i`, `a` or `o` types what's typed that many times: `3ix` Esc types `xxx`.

### The mouse

A click puts the cursor where it's clicked, and the wheel scrolls.

## Not yet

- Syntax colours, and everything a language server gives (errors, completion, going to definitions). They're next: grammars for [tree-sitter](https://tree-sitter.github.io) will load as WebAssembly, and language servers will run in the daemon.
- Line numbers. Long lines don't wrap: the view scrolls sideways to follow the cursor. A tab is always 4 columns wide.
- `$` and `l` stop at a line's last character that isn't blank, as on a terminal's screen, so blanks at a line's end can be reached only with `A` and `D`.
- Files with Windows line endings show `^M` at each line's end.
- `:e` opens a new tab, rather than replacing the file the pane shows, as Vim's does.
- `clackatoo edit` opens the tab, but the window doesn't switch to it.
- Only one register; no macros, marks, `:s`, `>>`, `~` or `%`.
- Dragging the mouse to select.
- A change typed just as the connection to the daemon drops can be lost.

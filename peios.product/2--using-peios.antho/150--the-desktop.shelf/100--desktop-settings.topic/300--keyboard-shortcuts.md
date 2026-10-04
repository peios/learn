---
title: Keyboard shortcuts
type: how-to
description: Change the desktop's keyboard shortcuts by pressing the keys you want, put them back, and set them for everyone — with every action, its id and its built-in default, and where each choice is kept in the registry.
related:
  - peios/desktop-settings/overview
  - peios/desktop-settings/for-all-users
  - peios/desktop-apps/settings-apps
---

The desktop's keyboard shortcuts work wherever the keyboard is, in any
window. Each **action**, such as moving to the next workspace, can have
several shortcuts, or none.

## Changing a shortcut

In Desktop Settings, **Keyboard Shortcuts** under **For You** lists every
action, grouped into **Launcher & Dock** and **Windows & Workspaces**, with
its shortcuts as keys.

- **+ Add**, then press the keys you want. Holding Ctrl or Alt on its own is
  waited past; press Esc, or click elsewhere, to stop without changing
  anything.
- **×** on a shortcut removes it. An action with none says **None**.
- **Reset** puts one action back to the System Default; **Reset All to
  System Default** puts them all back.

A shortcut must include Ctrl, Alt or Meta, since the desktop takes it from
every window, a text field included, and a key on its own is met while
typing. The browser keeps a few shortcuts for itself, such as Ctrl+W, Ctrl+T
and F11, and those can't be used. A shortcut already assigned to another
action is refused, with which; remove it there first.

**Open Dock Item** is set by modifiers, not a whole shortcut: `Alt` means
Alt+1 to Alt+9, one for each of the first nine items in the dock. To change
it, press **Change**, then hold the new modifiers and press any number.

Changes apply at once, in every window of yours.

## The actions

| Action | Id | Built-in default |
|---|---|---|
| Toggle Launcher | `Launcher` | Ctrl+Space, Alt+P |
| Open Dock Item | `DockItem` | Alt (with 1 to 9) |
| Focus Previous Tile | `PreviousTile` | Alt+J |
| Focus Next Tile | `NextTile` | Alt+K |
| Previous Workspace | `PreviousWorkspace` | Ctrl+Alt+←, Ctrl+Alt+J |
| Next Workspace | `NextWorkspace` | Ctrl+Alt+→, Ctrl+Alt+K |
| Move Window to Previous Workspace | `MoveToPreviousWorkspace` | Ctrl+Alt+Shift+←, Ctrl+Alt+Shift+J |
| Move Window to Next Workspace | `MoveToNextWorkspace` | Ctrl+Alt+Shift+→, Ctrl+Alt+Shift+K |

## Where they are kept

Each action's shortcuts are one `REG_SZ` value, named by its id, in:

| Key | Whose |
|---|---|
| `CurrentUser\Software\Fenestra\Shortcuts` | Yours |
| `Machine\Software\Fenestra\Shortcuts` | The machine's, for everyone who hasn't chosen |

Your value is used if there is one, else the machine's, else the built-in
default. The data is the shortcuts separated by spaces, each written as
its keys joined by `+`, for example `Ctrl+Alt+ArrowLeft Ctrl+Alt+J`.
**Open Dock Item**'s is its modifiers alone, such as `Alt` or `Ctrl+Alt`.

An empty value is an action with no shortcut, which is different from no
value, which leaves the next level in force. A value that isn't a
`REG_SZ`, or that holds anything that isn't a shortcut the desktop may
take, is ignored as a whole and the next level is used; nothing repairs
it.

```
$ reg set 'CurrentUser\Software\Fenestra\Shortcuts' Launcher 'sz:Ctrl+Space'
```

## Where to go next

- [Default apps](~peios/desktop-settings/default-apps)
- [Settings for all users](~peios/desktop-settings/for-all-users), for the
  machine's shortcuts

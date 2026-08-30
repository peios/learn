---
title: Atrium
type: concept
description: "The Peios web UI — log in from a browser and get a desktop served by the machine: apps, windows, a terminal, on port 8080."
related:
  - peios/services-and-jobs/overview
  - peios/networking/overview
---

**Atrium** is the Peios web UI. Point a browser at port 8080 of a
Peios machine — `http://<address>:8080` — and log in with a Peios
account; what you get is not a management panel but a desktop: a
launcher of applications, windows, and a terminal, all served by the
machine and running on it as you.

Logging in through Atrium is a real logon, the same one the console
performs: the machine's authority checks your credentials and your
session runs under your own identity. Every application you open, and
every command a terminal runs, is a process on the machine belonging
to you.

## The Toolbox and windows

The grid of tiles is the **Toolbox** — every installed application.
Click a tile to open it; right-click for more, including pinning it to
the sidebar and opening a second window. Open windows appear
individually in the sidebar; the coloured dots in a window's title bar
close (red) and minimise (yellow) it, macOS-style.

Opening the same app again focuses its existing window; "Open in new
window" on the right-click menu makes another.

## Two browsers, one desktop

Your desktop lives on the machine, not in the browser. Close the tab
and come back: everything is where it was. Open the same machine from
a second browser or device and you can log in again — each login is
its own desktop today.

## Keyboard

| Chord | Action |
|---|---|
| `Ctrl+K` | Search / command bar |
| `Alt+T` | Toolbox |
| `Alt+W` | Close window |
| `Alt+M` | Minimise window |
| `Alt+1`–`Alt+9` | Focus the Nth window |
| ``Ctrl+` `` | Cycle windows |

Some chords belong to the browser itself (`Ctrl+W`, `Ctrl+T`,
`Alt+Tab`) and never reach Atrium.

## The terminal

The Terminal app is your shell on the machine — the same shell a
console login gives you, in a window. Closing the window ends the
shell and everything it is running.

## Services

The Services app is service administration in a window: everything
peinit supervises, its state and health at a glance, and start, stop
and restart a click away. It acts with exactly your authority — it
runs `svctl` as you — so it takes an administrator's logon; peinit
refuses the connection to anyone else, and the app says so rather
than showing an empty room.

## Registry

The Registry app browses the machine's layered configuration: a tree
of hives on the left, a key's values in the middle, and an inspector
that shows where a value came from — the layer that won, and the
sequence it won at — before you change it. Edits are guarded: if a
value changes under you between reading and saving, the save is
refused and the app says so instead of overwriting blind. Like every
Atrium app it acts with exactly your authority — it runs `reg` as
you — so a key your logon may not open shows as denied, not as empty.

Atrium serves plain HTTP in this version: use it on networks you
trust.

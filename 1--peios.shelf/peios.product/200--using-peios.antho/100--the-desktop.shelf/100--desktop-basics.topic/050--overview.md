---
title: The Desktop
type: concept
description: The three programs behind a Peios desktop session, which state a session shares between devices, and where to start with windows, the dock, and settings.
related:
  - peios/signing-in/open-the-desktop
  - peios/desktop-basics/launcher-and-dock
  - peios/desktop-basics/windows-and-workspaces
  - peios/desktop-settings/overview
---

The Peios desktop runs in a web browser. You sign in to the machine from a
browser page, and the machine shows your desktop session there: application
windows, a dock, a launcher, and a top bar. The applications themselves run
on the Peios machine, with the authority of the account you signed in with.
Knowing which program provides each part tells you where to look when
something is missing or doesn't apply.

## The parts of a session

Three programs work together in every desktop session:

- **GXWI** serves the session. It presents the sign-in page, asks the
  machine's authentication service to check your credentials, and carries
  the session's traffic between your browser and the machine.
- **Fenestra** is the compositor. It tracks the applications in the session
  and arranges their windows into tiles and workspaces.
- **Fenesh** is the shell. It provides the background, top bar, dock,
  launcher, and power menu, and the Desktop Settings and Get started
  applications.

Fenestra and Fenesh run as your account, so they can do only what your
account can do. Fenestra starts whichever shell the machine is configured to
use. If none is configured, Fenestra shows its own minimal taskbar and
launcher instead. [The Desktop Shell](~peios/desktop-basics/the-shell) and
[The Desktop Compositor](~peios/desktop-basics/the-compositor) describe each
program in more detail.

## One session on several devices

You can open the same session from more than one device. Some state belongs
to the session, and some to each browser page:

| State | Belongs to |
|---|---|
| Open applications and their windows | The session |
| The workspace each window is on | The session |
| Window size, position, and focus | Each browser page |
| The workspace you are viewing | Each browser page |

Closing a window or moving it to another workspace therefore affects every
device attached to the session. A new window opens on the workspace that was
last selected on any device.

Closing a browser tab doesn't end the session. Sign in again to return to it,
or use the desktop's sign-out action to end it.

## Where to start

These guides cover everyday use of the desktop:

- [Using the Launcher and Dock](~peios/desktop-basics/launcher-and-dock) to
  start applications and switch between windows.
- [Arranging Windows and Workspaces](~peios/desktop-basics/windows-and-workspaces)
  to resize tiles and move between workspaces.
- [Desktop Settings](~peios/desktop-settings/overview) to change the
  wallpaper, clock, dock, and keyboard shortcuts.
- [Everyday Applications](~peios/everyday-apps/essential-apps) to find the
  application for a file, account, or system task.

If something doesn't appear or doesn't apply, start with
[Troubleshooting Desktop Settings and Applications](~peios/desktop-basics/troubleshooting)
or [Troubleshooting Windows and Desktop Connections](~peios/desktop-basics/troubleshooting-the-compositor).

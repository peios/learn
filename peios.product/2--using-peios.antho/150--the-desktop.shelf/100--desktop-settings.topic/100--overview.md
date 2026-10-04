---
title: Desktop Settings
type: concept
description: What Desktop Settings holds — your own wallpaper, clock, dock, keyboard shortcuts and default apps, and the machine's defaults for everyone — and how a person's choice, the machine's and the built-in default stack.
related:
  - peios/desktop-settings/wallpaper-clock-and-dock
  - peios/desktop-settings/keyboard-shortcuts
  - peios/desktop-settings/default-apps
  - peios/desktop-settings/for-all-users
---

**Desktop Settings** holds the settings of the desktop itself: GXWI, which
serves it, Fenestra, which draws and arranges its windows, and fenesh, the
shell with its top bar, dock and launcher. It ships with fenesh. Open it
from the launcher (type `desktop`).

Settings that belong to the machine rather than the desktop live in
System Settings, and a person's own account settings, such as their
password and language, in My Settings.

## For you, and for all users

The window has two groups of sections.

| Group | Sections | Kept in |
|---|---|---|
| **For You** | Wallpaper, Clock, Dock, Keyboard Shortcuts, Default Apps | Your own part of the registry, under `CurrentUser\` |
| **All Users** | Sign-In Screen, Desktop, Keyboard Shortcuts, Default Apps, Advanced | The machine's, under `Machine\` |

Anyone may change their own settings. The machine's are, as shipped,
for Administrators to change; anyone else sees them read-only, with the
reason said once at the top of the section.

## How the choices stack

Most settings exist at three levels, and the nearest one that is set
wins:

1. **Your choice**, if you have made one.
2. **The machine's**, set under All Users, for everyone who hasn't
   chosen.
3. **The built-in default**, what Peios does when nobody has chosen.

Desktop Settings calls the second and third together the **System
Default**: choosing System Default for yourself removes your choice, so
the machine's (or the built-in) applies to you again.

## Changes apply at once

A switch or a choice from a list applies the moment it is made; a typed
value applies with the **Apply** button that appears beside it once it
has changed. What a change did is said along the bottom of the window.
Changes that could cut people off, such as the address GXWI listens on,
ask first, under their row.

## Where to start

- [Wallpaper, clock and dock](~peios/desktop-settings/wallpaper-clock-and-dock)
- [Keyboard shortcuts](~peios/desktop-settings/keyboard-shortcuts)
- [Default apps](~peios/desktop-settings/default-apps)
- [Settings for all users](~peios/desktop-settings/for-all-users)

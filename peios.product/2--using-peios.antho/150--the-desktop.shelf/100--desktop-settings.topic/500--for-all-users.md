---
title: Settings for all users
type: how-to
description: The machine's desktop settings — the sign-in screen, everyone's wallpaper, clock, pins and icon themes, everyone's shortcuts and default apps, and the programs that make up the desktop — and where each is kept.
related:
  - peios/desktop-settings/overview
  - peios/desktop-settings/wallpaper-clock-and-dock
  - peios/desktop-settings/keyboard-shortcuts
  - peios/desktop-settings/default-apps
---

The **All Users** sections of Desktop Settings set the machine's choices:
what everyone has until they choose their own, and the parts of the
desktop that are the machine's alone. Changing them needs write access to
the keys below, which as shipped only Administrators have. Anyone else
sees them read-only, with the reason said once.

## Sign-In Screen

- **Machine Name** is the name the sign-in screen shows, up to 64
  characters. It is separate from the machine's network name, which is
  System Settings'. Empty is the System Default.
- **Notice** is text shown under it, such as an acceptable-use notice:
  **Change…** opens it, up to eight paragraphs separated by blank lines and
  2,000 characters in all.

Both apply when GXWI next starts. They are `Machine\Software\GXWI\Logon`
`Name` (`REG_SZ`) and `Notice` (`REG_MULTI_SZ`, a paragraph each).

## Desktop

- **Wallpaper** chooses everyone's from the same pictures as your own.
- **Time Format** is everyone's clock, 24-hour unless chosen.
- **Pinned Apps** shows everyone's dock; **Use My Pins** makes the dock
  you have now everyone's.

These are `Wallpaper`, `ClockHours` and `Pinned` in `Machine\Software\fenesh`,
the same values as a person's own (see [wallpaper, clock and
dock](~peios/desktop-settings/wallpaper-clock-and-dock)).

- **Icon Themes** are the icon themes desktop apps use, in order of
  preference, each a folder in `/usr/share/icons`; the base theme is always
  used last. They are `Machine\Generic\Icons` `Themes` (`REG_MULTI_SZ`), and
  apply to new desktop sessions.

## Keyboard Shortcuts and Default Apps

These work as the personal sections do, but set the machine's choices:
`Machine\Software\Fenestra\Shortcuts` and
`Machine\Generic\Applications\Defaults`. **Reset All to Built-In** removes
the machine's shortcuts, and **First Available** removes the machine's
default for a type. See [keyboard shortcuts](~peios/desktop-settings/keyboard-shortcuts)
and [default apps](~peios/desktop-settings/default-apps).

## Advanced

The programs that make up the desktop, and how GXWI serves it. Leave a
field empty for the System Default.

| Setting | Is | Kept in |
|---|---|---|
| **Listen Address** | The address and port GXWI serves on. The default, `127.0.0.1:7780`, is reachable only from this machine. | `Machine\Software\GXWI` `Listen` |
| **Compositor** | The program each desktop session runs, as its user. Default `/usr/bin/fenestra`. | `Machine\Software\GXWI` `Compositor` |
| **Shell** | The programs that provide the panels, dock and launcher, separated by spaces. Default `/usr/bin/fenesh`. | `Machine\Software\Fenestra` `Shell` |
| **Overlay** | A program shown to everyone in place of the sign-in screen, such as an installer. | `Machine\Software\GXWI` `OverlaySession` |
| **Overlay Account** | The account the overlay runs as. | `Machine\Software\GXWI` `OverlayUsername` |

Each of these is trusted with every person's desktop, so **Review
Changes…** shows what changes and what it means before **Apply Changes**.
A new listen address takes effect when GXWI next starts, and pages open on
the old one, including Desktop Settings, lose the desktop. While an
overlay is set, nobody can sign in or reach a desktop.

## Where to go next

- [Desktop Settings](~peios/desktop-settings/overview)

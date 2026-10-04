---
title: Wallpaper, clock and dock
type: how-to
description: Choose your wallpaper from the pictures Peios ships or one of your own, set the top bar's clock to 12 or 24 hours, and go back to the System Default dock, in Desktop Settings or the registry.
related:
  - peios/desktop-settings/overview
  - peios/desktop-settings/for-all-users
---

These are the **For You** sections of Desktop Settings. Each applies to you
alone, and only once you have chosen: until then you have the machine's
choice, and failing that the built-in one.

## Wallpaper

**Wallpaper** shows the pictures you can choose from:

- **System Default**, the machine's wallpaper, or the built-in one when the
  machine has none;
- the wallpapers Peios ships, **Diamond Beach Dark** (the built-in one) and
  **Diamond Beach Light**, kept in `/usr/share/wallpapers/peios`;
- your own picture, once you have chosen one.

Click one to use it. **Choose Picture…** opens the file dialog for a
picture of your own: a PNG, JPEG, SVG, WebP, AVIF or GIF of up to 16 MB,
that you can read. The desktop changes at once, on every screen you are
signed in on.

The choice is the picture's path, `CurrentUser\Software\fenesh` `Wallpaper`
(`REG_SZ`). Deleting the value is System Default. A path that can't be
read, isn't a picture or is too large is ignored and the next level down
is used.

## Clock

**Time Format** sets how the clock in the top bar counts the hours:
**24-Hour (14:05)**, **12-Hour (2:05 PM)**, or **System Default**, which is
the machine's choice, else 24-hour. It is `CurrentUser\Software\fenesh`
`ClockHours`, a `REG_DWORD` of 12 or 24; any other number is ignored.

The clock shows the time in the machine's time zone, which is set in
System Settings; see [the time zone](~peios/time/time-zone-and-setting-the-clock).

## Dock

The apps pinned to your dock are changed from the dock and the launcher
themselves: right-click an app to pin or unpin it, and drag a pin to move
it. Your first change makes your own set; until then the dock shows the
machine's pins.

**Dock** shows whose pins you have. **Use System Default** throws your own
set away, so the machine's applies to you again. Your set is
`CurrentUser\Software\fenesh` `Pinned`, a `REG_MULTI_SZ` of application ids
in order.

**Get Started**, under **Show Again**, opens the welcome you saw on your
first sign-in, and shows it again at your next one if it can't open now.

## Where to go next

- [Keyboard shortcuts](~peios/desktop-settings/keyboard-shortcuts)
- [Settings for all users](~peios/desktop-settings/for-all-users), where an
  administrator sets the machine's wallpaper, clock and pins

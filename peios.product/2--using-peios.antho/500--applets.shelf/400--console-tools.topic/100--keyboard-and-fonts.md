---
title: Console keyboards and fonts
type: guide
description: Use kbd to inspect and configure a Linux virtual console on Peios.
---

`org.kernel.kbd` supplies the upstream kbd console tools. Its matching
`org.kernel.kbd-common` package supplies keymaps, fonts, translations and
manual pages. Console data lives under `/usr/share/kbd`.

These tools operate on Linux virtual consoles: the text screens associated
with devices such as `/dev/tty1`. They do not configure a keyboard layout in
an SSH client, a serial terminal, or a graphical application.

## Inspect a keymap without applying it

Generate a binary keymap from the installed UK layout:

```sh
loadkeys --bkeymap uk > uk.bmap
```

This parses the map and its includes without changing the console. The
package also includes layouts such as `us`, `de` and `fr`.

## Configure a console

With a token authorized for the console operation, apply a keyboard map or
load a font:

```sh
loadkeys -C /dev/tty1 uk
setfont -C /dev/tty1 Lat2-Terminus16
```

The kernel determines access. Installing kbd does not grant console
privileges, and the tools are not installed setuid. Keymap changes can
affect other virtual consoles; selecting a device is not a promise of a
separate per-session keyboard layout.

`dumpkeys` inspects the current map, `kbd_mode` inspects or changes the
keyboard mode, and `fgconsole` reports the active virtual console. `chvt`
switches consoles. Switching to a console does not create a login session.

## Package scope

Installation does not select a default keymap or font, add boot services,
or start additional login prompts. Persistent console settings and
multi-console logins require separate system configuration.

The PAM-based `vlock` screen locker and optional XKB-to-console conversion
are disabled. Native kbd keymaps remain available. `openvt` is a process
launcher for a virtual console. It preserves the caller's Peios token and
the console device's existing security descriptor. It does not grant an
identity or authenticate a user. Its `--user` mode is explicitly rejected
on Peios; that upstream mode infers a numeric user and invokes `login -f`. Use peinit and the authenticated login
service for managed login sessions.

The `-debuginfo`, `-debugsource` and `-source` packages provide debugging
symbols, referenced source files and corresponding source respectively.

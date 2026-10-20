---
title: Configuring Console Keyboards and Fonts
type: how-to
description: Apply a Linux virtual-console map and distinguish stored boot preferences from a successful live load.
---

The kbd tools operate on Linux virtual consoles such as `/dev/tty1`. They do
not change an SSH client's keyboard, a serial terminal, or the browser's
layout. Install `org.kernel.kbd` and its matching common data package;
keymaps and fonts live under `/usr/share/kbd`.

## Inspect and apply

1. To parse an installed layout without changing the console, generate a
   binary map: `loadkeys --bkeymap uk > uk.bmap`.
2. With authority for the console operation, apply the intended map:

   ```sh
   loadkeys -C /dev/tty1 uk
   ```

3. Verify typing at the machine's text console. A map can affect other
   virtual consoles; a device selection is not a per-session layout promise.

`setfont -C /dev/tty1 Lat2-Terminus16` loads an installed font when permitted.
`dumpkeys` inspects the map, `kbd_mode` inspects or changes keyboard mode,
`fgconsole` identifies the active console, and `chvt` switches consoles.
Switching is neither authentication nor creation of a logon session.

## Store a boot preference

The `console-keymap` service reads the `Keymap` name under
`Machine\System\Console`. A name selects installed data, never an arbitrary
path. With the registry and service-control rights, adapt:

```sh
reg set Machine/System/Console Keymap sz:uk
svctl restart console-keymap
```

System Settings offers the corresponding **Console Keyboard** layout
selection and requests a restart when available and permitted. A custom
image without the service does not acquire a loader by storing a value.
A configured boot-triggered service can apply the choice at next boot when
an immediate restart is unavailable. An absent value leaves the built-in US
layout; an invalid map leaves the existing layout and produces a diagnostic.

Inspect service status/output and verify actual console input. A saved value
or accepted restart request does not establish that loading finished. Font
persistence requires separate configuration. Installing kbd alone neither
applies its service seed nor starts additional sign-in prompts.

## Launch and package boundaries

`openvt` launches with the caller's token and the existing console descriptor;
it does not authenticate or grant identity. Its upstream `--user` mode is
rejected on Peios. Use the [managed console sign-in
services](~peios/terminal-sign-in/using-a-console) for that purpose.
The PAM-based vlock locker and optional XKB conversion are excluded from the
recipe. Debug and source packages do not configure the console.

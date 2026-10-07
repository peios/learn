---
title: Another machine
type: reference
description: With --remote, the window and the clackatoo command use the daemon on another machine, reached with ssh. How it connects, what the other machine needs, and what happens when the connection drops.
related:
  - clackatoo/reference/window
  - clackatoo/reference/cli
---

The window and the `clackatoo` command can use the daemon on another machine instead of this one: your desktop from your laptop, or a server. The terminals run there, and keep running when you disconnect.

```sh
clackatoo --remote desktop                  # a window on desktop's newest terminal
clackatoo list --remote desktop             # its terminals
clackatoo new --remote jack@server -- htop  # start one there
```

The host is anything `ssh` accepts: a hostname, `user@host`, or a name from your `~/.ssh/config`, where ports, keys and jump hosts belong.

## How it connects

`--remote host` runs `ssh host clackatoo bridge`. On the other machine, the bridge starts the daemon if it isn't running, then passes everything between ssh and the daemon. ssh does the logging in and the encryption, so clackatoo opens no network port of its own, and anyone who can use the daemon could already log in to that machine as you.

The bridge only passes bytes along. The window or command checks that the daemon on the other machine speaks its version of the protocol, as it does on this one.

## What the other machine needs

- **clackatoo, built from the same version.** A daemon from another build speaks another protocol, which the window [offers to replace](#a-daemon-from-another-build).
- **clackatoo on the PATH ssh's commands get.** That is often shorter than an interactive shell's, and may leave out `~/.cargo/bin` or `~/.local/bin`. If it isn't there, the error is the remote shell's "command not found". `--remote-command` names it instead:

  ```sh
  clackatoo --remote desktop --remote-command ~/.cargo/bin/clackatoo
  ```

  The command is run by the remote shell, so it can be any command line that ends by running clackatoo, such as `env XDG_RUNTIME_DIR=/tmp/ck clackatoo`. Setting `CLACKATOO_REMOTE_COMMAND` saves typing it each time.

- **Logging in without typing anything, for the window.** A window opened from your desktop's launcher has no terminal for ssh to ask for a password or a key's passphrase, so ssh fails with "Permission denied". Use a key loaded into `ssh-agent`. The `clackatoo` command, run in a terminal, can ask.

- **On a server nobody is logged in to:** systemd removes your runtime directory (`/run/user/<uid>`) when your last session ends, taking the daemon's socket with it. The daemon keeps running, but the next connection can't find it and starts another. Run this once on the server so your runtime directory stays:

  ```sh
  loginctl enable-linger
  ```

## Options

| Option | Environment variable | |
|---|---|---|
| `--remote <HOST>` | | Use the daemon on `HOST`. |
| `--remote-command <COMMAND>` | `CLACKATOO_REMOTE_COMMAND` | The command that runs clackatoo on the other machine. Default: `clackatoo`. |
| | `CLACKATOO_SSH` | The program run as ssh. Default: `ssh`. It is given ssh's options, then `--`, the host and the command. |

clackatoo passes ssh a few options of its own:

- `-T`: no terminal on the other end; the bridge doesn't want one.
- `ConnectTimeout=10`: an unreachable host fails after 10 seconds.
- `ServerAliveInterval=5` and `ServerAliveCountMax=3`: a connection that has died, such as when the laptop sleeps or changes network, is noticed within 15 seconds.

## When the connection drops

The window says it lost the connection, and why:

- Enter reconnects, to the same terminal if it's still running. The window keeps its mode, its scroll position and the history it fetched.
- Esc quits.

Nothing on the other machine stops when the connection drops: the terminals carry on, and output that arrives meanwhile is there when you reconnect.

A connection doesn't yet survive a change of network, such as moving from home Wi-Fi to a phone's hotspot. ssh's connection dies, and the window says so.

## A daemon from another build

If the daemon on the other machine speaks another version of the protocol, the window says so, as it does [on this machine](~clackatoo/reference/window#a-daemon-from-another-build). Enter replaces that daemon using the clackatoo installed there, closing its terminals. If that clackatoo is itself from another build, the window says to update it.

The `clackatoo` command doesn't replace anything. Running `clackatoo stop` on the other machine stops its daemon.

## Two windows on one terminal

A terminal has one size, so when windows of different sizes show the same terminal, such as your laptop's and your desktop's, they take turns: the terminal takes the size of whichever window last opened on it, was resized or was focused.

## Typing over a slow connection

Every key goes to the other machine and back before it shows, so a connection with 100 ms round trips shows each key 100 ms late. On a local network this is a millisecond or two.

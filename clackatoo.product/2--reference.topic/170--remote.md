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
clackatoo --remote desktop                  # a window on desktop's workspaces
clackatoo list --remote desktop             # its terminals
clackatoo new --remote jack@server -- htop  # start one there
```

The host is anything `ssh` accepts: a hostname, `user@host`, or a name from your `~/.ssh/config`, where ports, keys and jump hosts belong.

## How it connects

`--remote host` runs `ssh host clackatoo bridge`. On the other machine, the bridge starts the daemon if it isn't running, then passes everything between ssh and the daemon.

Through it, the window or command first checks that the daemon speaks its version of the protocol, as it does on this one. Then the two talk over QUIC, a network protocol that runs several independent streams over one connection, carried inside the ssh connection.

ssh does the logging in, and it's how each end knows the other is genuine. The daemon only takes QUIC connections that come through ssh, and the window only trusts the certificate the daemon sent it through ssh. So clackatoo opens no network port of its own, and anyone who can use the daemon could already log in to that machine as you.

Inside ssh, QUIC doesn't change anything you'd notice yet. It's the groundwork for two things to come:

- Giving each terminal a stream of its own, so a flood of output in one never holds up typing in another.
- Moving the connection out of ssh onto UDP when the network allows, so that it survives your laptop changing networks.

## What the other machine needs

- **clackatoo, built from the same version.** A daemon from another build speaks another protocol, which the window [offers to replace](#a-daemon-from-another-build).
- **clackatoo on the PATH ssh's commands get.** That is often shorter than an interactive shell's, and may leave out `~/.cargo/bin` or `~/.local/bin`. If it isn't there, the error is the remote shell's "command not found". `--remote-command` names it instead:

  ```sh
  clackatoo --remote desktop --remote-command ~/.cargo/bin/clackatoo
  ```

  The command is run by the remote shell, so it can be any command line that ends by running clackatoo, such as `env XDG_RUNTIME_DIR=/tmp/ck clackatoo`. Setting `CLACKATOO_REMOTE_COMMAND` saves typing it each time.

- **A way to log in.** A key loaded into `ssh-agent` logs in without asking anything. Otherwise, the window asks for ssh's password, or the key's passphrase, itself, in place of the terminal, and asks again on every reconnect. It also asks whether to trust a host ssh hasn't seen before. The `clackatoo` command leaves ssh to ask on the terminal it runs in.

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

[`clackatoo ping --remote host`](~clackatoo/reference/cli#ping) measures it: how long the daemon takes to answer, and how long a key takes to come back from a program. clackatoo's own share is small. Through ssh to the same machine, where the network costs next to nothing, a key comes back in about a third of a millisecond, so nearly all of anything above that is the network.

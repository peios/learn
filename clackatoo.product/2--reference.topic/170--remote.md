---
title: Another machine
type: reference
description: With --remote, the window and the clackatoo command use the daemon on another machine, reached with ssh. How it connects, how it moves onto UDP to survive network changes, what the other machine needs, and what happens when the connection drops.
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

ssh does the logging in, and it's how each end knows the other is genuine. The daemon only takes QUIC connections that come through ssh, and the window only trusts the certificate the daemon sent it through ssh. Anyone who can use the daemon could already log in to that machine as you.

Each terminal's screen updates come on a QUIC stream of their own, apart from everything else, so a lost packet holds up only the terminal it belonged to.

## Moving onto UDP

Once connected, the window or command tries reaching the daemon straight over UDP, at the address ssh reached that machine at. If that works, the connection moves there, out of ssh:

- **It survives your network changing,** such as moving from home Wi-Fi to a phone's hotspot, or a short sleep. ssh's connection dies when that happens; the QUIC connection carries on from the new network, and the window doesn't notice.
- **Keys come back a little faster,** with ssh out of the way.

It finds out with a few probes, small datagrams the daemon sends straight back, while the connection carries on inside ssh, so nothing waits on the attempt. If none comes back within two seconds, as when a firewall blocks UDP, the connection stays inside ssh. If UDP stops getting through later, the connection goes back into ssh after about ten seconds, if ssh's connection is still up, and tries UDP again a minute after.

[`clackatoo ping --remote host`](~clackatoo/reference/cli#ping) says which way each round went: `(over UDP)` or `(through ssh)`.

The daemon takes UDP on the first free port from 60000 to 61000, the same range as mosh, when the first connection through ssh arrives. It never takes a new connection over UDP, only packets for connections already set up through ssh. Probes carry a key the daemon only gives out through ssh, and it answers nothing else, so the port gives nothing away to a scan.

### Firewalls

A firewall on the other machine has to let UDP in on those ports. If it already does for mosh, there's nothing to do. Otherwise, with `ufw`:

```sh
sudo ufw allow 60000:61000/udp
```

or with `firewalld`:

```sh
sudo firewall-cmd --permanent --add-port=60000-61000/udp && sudo firewall-cmd --reload
```

To use other ports, or none, set `CLACKATOO_UDP_PORTS` for the daemon on the other machine: a port, a range such as `60100-60200`, or `off` to keep every connection inside ssh. The daemon reads it when it starts, and one started by `--remote` gets it from the remote command:

```sh
clackatoo --remote server --remote-command 'env CLACKATOO_UDP_PORTS=60100-60200 clackatoo'
```

Through a jump host (`ProxyJump`), ssh reached the other machine at an address on its own network, which you usually can't reach directly, so the connection stays inside ssh.

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
- `ServerAliveInterval=5` and `ServerAliveCountMax=3`: a connection that has died, such as when the laptop sleeps or changes network, is noticed within 15 seconds. A connection that has moved onto UDP carries on without it.

## When the other machine stops answering

If what the window sends goes unanswered for about three seconds, a red notice at the right of the top bar says so: `No contact with desktop for 12 s`, counting up. The window stays as it was, and anything you type waits to be sent. The notice goes as soon as the other machine answers again, as when your laptop finds a network.

An idle window notices within about half a minute, at its next keep-alive.

## When the connection drops

A connection inside ssh drops when ssh's does. One on UDP drops after ten minutes without hearing from the other end, such as a laptop asleep for longer than that. An idle window stays connected: it sends the daemon a few bytes every 25 seconds, which also keeps your router from forgetting the connection.

When the connection drops, the window says so, and why:

- Enter reconnects, to the same terminal if it's still running. The window keeps its mode, its scroll position and the history it fetched.
- Esc quits.

Nothing on the other machine stops when the connection drops: the terminals carry on, and output that arrives meanwhile is there when you reconnect.

## A daemon from another build

If the daemon on the other machine speaks another version of the protocol, the window says so, as it does [on this machine](~clackatoo/reference/window#a-daemon-from-another-build). Enter replaces that daemon using the clackatoo installed there, closing its terminals. If that clackatoo is itself from another build, the window says to update it.

The `clackatoo` command doesn't replace anything. Running `clackatoo stop` on the other machine stops its daemon.

## Two windows on one terminal

A terminal has one size, so when windows of different sizes show the same terminal, such as your laptop's and your desktop's, they take turns: the terminal takes the size of whichever window last opened on it, was resized or was focused.

## Typing over a slow connection

Every key goes to the other machine and back before it shows, so a connection with 100 ms round trips shows each key 100 ms late. On a local network this is a millisecond or two.

[`clackatoo ping --remote host`](~clackatoo/reference/cli#ping) measures it: how long the daemon takes to answer, and how long a key takes to come back from a program. clackatoo's own share is small. To the same machine, where the network costs next to nothing, a key comes back in about a fifth of a millisecond over UDP, and a third through ssh, so nearly all of anything above that is the network.

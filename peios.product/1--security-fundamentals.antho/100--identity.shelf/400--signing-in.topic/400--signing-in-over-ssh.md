---
title: Signing in over SSH
type: how-to
description: The SSH server — turning it on and off, moving its port, refusing passwords so only keys sign in, and checking its host key — with the ssh-settings command or SSH Settings on the desktop.
related:
  - peios/signing-in/overview
  - peios/managing-local-principals/lps-command
  - peios/networking/network-policy
  - peios/network-objects/port-reservations
  - peios/services-and-jobs/controlling-services
---

The SSH server lets people sign in to this machine from another over the network, with their password or one of their SSH keys. It is the `sshd` service, from the `dev.peios.openssh` package. Every SSH sign-in is a `RemoteInteractive` logon through the same authority as any other: see [Signing in](~peios/signing-in/overview).

Four things about the server are settings:

| Setting | Where it is | Shipped as |
|---|---|---|
| Whether it runs | the `sshd` service's `Disabled` value | on, on images that include the service |
| Its port | `Machine\Software\OpenSSH` `Port` (`REG_DWORD`) | 22 |
| Whether it accepts passwords | `Machine\Software\OpenSSH` `PasswordAuthentication` (`REG_DWORD`, 0 or 1) | 1 |
| Its host key | `/var/state/sshd/ssh_host_ed25519_key`, made on first start | — |

The port and password sign-in are machine policy in the registry, not lines of `sshd_config`. `start-sshd` reads them each time the service starts and gives them to `sshd` on its command line, and a `Port` or `PasswordAuthentication` line in `/lcl/etc/ssh/sshd_config` has no effect. Other `sshd` options still go in that file.

Change them with **`ssh-settings`** on a terminal, or **SSH Settings** on the desktop (type `ssh` in the launcher), which is the same program and does the same things.

## Looking

```
$ ssh-settings
server       running
port         22
passwords    accepted
host key     SHA256:Wm3…
```

Anyone may look, except at the host key, which only SYSTEM and Administrators may read; others see why instead.

## Turning it on and off

```
ssh-settings on
ssh-settings off
```

`on` sets the service to start at boot and starts it now; `off` stops it and keeps it from starting. People signed in over SSH are disconnected when it stops. Each needs write access to the service's key, `Machine\System\Services\sshd`, and the right to start and stop `sshd`, which as shipped only Administrators have; see [who can manage a service](~peios/services-and-jobs/who-can-manage-a-service). Without the second, the setting is still saved and takes effect at the next boot, and you are told so.

## Moving the port

```
ssh-settings port 2222
```

A port is three things that must agree, and `ssh-settings` changes all three in one registry transaction, so none is ever moved without the others:

- the `Port` value;
- `sshd`'s **port reservation**, the descriptor under `Machine\System\Network\TcpIp\PortReservations` that lets only `sshd` bind the port (see [port reservations](~peios/network-objects/port-reservations));
- the `ssh` firewall rule, `Machine\System\Network\Rules\Flow\ssh`, whose `DstPort.Equal` is the port let in (see [network policy](~peios/networking/network-policy)).

It then restarts `sshd` onto the new port, which disconnects everyone signed in over SSH, you too if you are. Connect again on the new port: `ssh -p 2222 alice@host`.

A port another program has reserved is refused: a reservation naming that one port and nothing else, such as `tcp:80` for a web server, makes it that program's. A wider range that contains the port, such as `tcp:1-1023`, is fine, since reservations nest. Moving the port needs write access to all three keys, which as shipped only Administrators have.

## Keys only

```
ssh-settings passwords off
```

With passwords off, only keys sign in over SSH. An account whose credential policy is `password` then cannot sign in over SSH at all, though it still signs in at the console and on the desktop. Before turning passwords off, make sure the people who need SSH have a key and a policy of `key` or `either`: each person adds their own keys in My Settings, or an administrator adds them with [`lps key add`](~peios/managing-local-principals/lps-command) and sets the policy with `lps policy`. `ssh-settings passwords on` lets passwords in again. Either restarts `sshd`.

## The host key

```
ssh-settings fingerprint
```

The first time someone connects, their SSH client shows the server's host key fingerprint and asks whether to trust it. Compare it with this one, read on the machine itself or by someone you trust who can read it, before answering yes. The key is made on the server's first start and never replaced automatically.

## On the desktop

SSH Settings shows the same four things on one page: the server, with how it is and a switch to turn it on or off; **Port**, with **Apply** once it is changed; **Accept passwords**, as a switch; and **Host key**, with **Copy**. Turning the server on happens at once. Anything that restarts or stops it — turning it off, moving the port, password sign-in either way — ends every SSH session, so it asks first, under its row, and changes nothing until it is told to go ahead. What you may not change is shown read-only, with the reason, once. Each change says what it did along the bottom of the window, including whether `sshd` was restarted.

## Exit status

| Code | Meaning |
|---|---|
| 0 | Done, or shown. |
| 1 | The change was refused or failed; the reason is printed. |
| 64 | The command line was wrong. |

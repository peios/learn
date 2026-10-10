---
title: Signing in over SSH
type: how-to
description: Verify a first SSH connection, preserve administrator access when disabling SSH passwords, and manage the server, port and host key with ssh-settings or SSH Settings.
related:
  - peios/signing-in/overview
  - peios/managing-local-principals/lps-command
  - peios/networking/network-policy
  - peios/network-objects/port-reservations
  - peios/services-and-jobs/controlling-services
---

The SSH server lets people sign in to this machine from another over the network, with their password or one of their SSH keys. It is the `sshd` service, from the `dev.peios.openssh` package. Every SSH sign-in is a `RemoteInteractive` logon through the same authority as any other: see [Signing in](~peios/signing-in/overview).

That includes commands without a PTY and SFTP: the account must permit `remote-interactive`, not just `network`. An account with credential policy `none` cannot sign in over SSH. Password authentication requires an actual password and a policy allowing it; key authentication requires an enrolled key and a policy of `key` or `either`. The [SSH implementation contract](~peios/logon/ssh-public-key-authentication) records the release-qualification and compatible-build requirements.

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

## Connect from another computer

1. From a trusted administrator session on the Peios console, or a [certificate-verified GXWI session](~peios/signing-in-from-a-browser/the-certificate) as an administrator, read the machine's address, SSH service state, port and host fingerprint:

   ```
   net status
   ssh-settings
   ssh-settings fingerprint
   ```

   Check that the server is running. Choose an address on an interface reachable from the other computer; [Reading `net status`](~peios/networking/the-net-command#reading-net-status) explains the interface blocks. For a direct connection, use the port shown by `ssh-settings`, which is 22 as shipped. The QEMU Makefile's host-forwarded port 2222 is a separate route described in the [build quick start](~peios/peiso/building-images/quick-start#open-the-web-desktop).

2. On the other computer, use your account name, the machine's address and that observed port:

   ```
   ssh -p <observed-port> <name>@<machine-address>
   ```

   Before accepting a first-connection prompt, compare its SSH host fingerprint with the trusted reading from step 1. This is the SSH host key, not GXWI's TLS certificate fingerprint. If they differ, stop and investigate; do not accept the key or discard a remembered key just to suppress a warning.

3. Sign in with the intended password or enrolled key and check that a **new shell opens**. A running service or an already-open session alone does not prove that a new sign-in works.

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

`ssh-settings passwords off` disables password authentication **for SSH**. It does not require an account-wide policy of `key`. Keep the account policy `either` when its password must also work through GXWI: [GXWI does not currently offer SSH-key authentication](~peios/peiso/building-images/quick-start#open-the-web-desktop), so a `key`-only account cannot use that sign-in path.

With SSH passwords off, an account whose policy is `password` cannot sign in over SSH, though it can still use its password at the console and on the desktop, subject to its other sign-in restrictions.

Before changing the server:

1. Enroll a key for each person who needs SSH. They can use My Settings where permitted, or an administrator can use [`lps key add <name> <public-key-file> [label]`](~peios/managing-local-principals/lps-command#credentials-and-ssh-keys). Adding a key does not change credential policy. For a password-enabled account that will also use keys, an administrator sets `lps policy <name> either`; retain that policy if GXWI password access is needed.
2. Inspect `lps show <name>` and `lps key list <name>` to check the enabled account, enrolled key, credential policy and permitted `remote-interactive` logon type. While SSH passwords are still available, make a **fresh SSH connection that actually authenticates with the enrolled key**, following the host-key check above. A connection that falls back to a password does not count as a key test. If the key test fails, stop before disabling passwords and check those account settings and the service state.
3. Verify a fresh administrator sign-in through a separate **non-SSH** route, such as the local console or certificate-verified GXWI, and keep that route available. The [last-administrator guard](~peios/managing-local-principals/creating-accounts#the-last-administrator-guard) does not prove that a usable route exists. Keeping another SSH session open is insufficient: this change restarts `sshd` and ends **every SSH session**.

Only after both access paths work, disable SSH passwords:

```
ssh-settings passwords off
```

Then make another new key-authenticated SSH connection and verify that its shell opens. If it fails, use the surviving console or GXWI administrator route to inspect the settings and restore SSH password acceptance with `ssh-settings passwords on`. This reversal also restarts `sshd`; it does not change account credential policy. Keep the separate administration route until fresh SSH access has been verified again.

## The host key

```
ssh-settings fingerprint
```

The first time someone connects, their SSH client shows the server's host key fingerprint and asks whether to trust it. Compare it with this one, read on the machine itself or by someone you trust who can read it, before answering yes. The key is made on the server's first start and never replaced automatically.

## On the desktop

SSH Settings shows the same four things on one page: the server, with how it is and a switch to turn it on or off; **Port**, with **Apply** once it is changed; **Password Authentication**, as a switch; and **Host Key Fingerprint**, with **Copy**. Turning the server on happens at once. Anything that restarts or stops it — turning it off, moving the port, password sign-in either way — ends every SSH session, so it asks first, under its row, and changes nothing until it is told to go ahead. What you may not change is shown read-only, with the reason, once. Each change says what it did along the bottom of the window, including whether `sshd` was restarted.

## Exit status

| Code | Meaning |
|---|---|
| 0 | Done, or shown. |
| 1 | The change was refused or failed; the reason is printed. |
| 64 | The command line was wrong. |

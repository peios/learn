---
title: Driving a machine
type: how-to
description: Booting a Peios machine with a vsock device, pointing the dwe client at it, and running commands, moving files and detaching long work that outlives the connection.
related:
  - peios/dwe/what-dwe-is
  - peios/dwe/protocol
  - peios/debugging-the-kernel/kernel-tracepoints
---

This page assumes an image built with the `peios-dwe` package and its service seed applied. If you are not sure, [What DWE is](~peios/dwe/what-dwe-is) explains why both are needed and why neither is the default.

## Give the machine a transport

`dwed` binds a vsock listener at boot, but a guest cannot conjure the transport itself — the hypervisor has to give it a vsock device. Under QEMU that is one flag:

```sh
-device vhost-vsock-pci,guest-cid=3
```

The context id is how the host addresses this guest. Any value of 3 or above works; QEMU refuses to start if another running guest already holds the one you picked, so concurrent machines need distinct ids.

In the Peios tree, `make boot-dwe` is `make boot` with that device attached:

```sh
cd dist/release
make iso-dwe               # build the DWE medium (once; no root needed)
make boot-dwe              # or: make boot-dwe DWE_CID=4
```

Leave it running. Unlike a scripted boot, the point is that the machine stays up.

> [!NOTE]
> `/dev/vhost-vsock` is owned by `root:kvm`, so membership of the `kvm` group is enough — this does not need root.
>
> On a guest booted *without* a vsock device, `dwed` reports that it has no transport and exits cleanly. That is not an error and does not restart-loop.

## Point the client at it

The `dwe` client takes its target from `--target` or from `DWE_TARGET`:

```sh
export DWE_TARGET=vsock:3:4820        # a VM by context id
export DWE_TARGET=tcp:10.0.0.5:4820   # or over the network
```

The port defaults to 4820 and can be left off. Confirm you have the machine you think you have:

```console
$ dwe info
dwed            0.1.0
protocol        1
boot id         79880a4b-e3d0-4992-bea2-eb56f3839711
uptime          193s
```

The **boot id** is worth reading. It changes on every boot, so it is how you tell "the machine rebooted under me" from "my connection dropped" — two situations that otherwise look identical and mean very different things.

## Run something

```console
$ dwe exec -- ls -l /system
$ dwe exec --cwd /tmp -- ./probe
```

Everything after `--` is the argument vector, executed **directly**. There is no shell, so nothing re-interprets your quoting, globs your arguments or splits them on spaces. When you want a shell, ask for one:

```sh
dwe exec -- sh -c 'for p in /proc/[0-9]*; do cat $p/comm; done'
```

Two behaviours matter more than they look:

**The exit status is yours.** `dwe exec` exits with the guest command's status, so ordinary shell chaining works:

```sh
dwe exec -- test -f /etc/hostname && echo "it is there"
```

A command killed by a signal exits `128+N`, matching shell convention, so it is distinguishable from one that merely failed.

**The streams stay apart.** The guest's `stdout` and `stderr` are written to *your* `stdout` and `stderr`, still separated, as raw bytes:

```console
$ dwe exec -- ls /nonexistent 2>errors.txt
$ cat errors.txt
ls: cannot access '/nonexistent': No such file or directory
```

## Move files

```sh
dwe pull /var/log/peinit.log ./peinit.log   # out of the guest
dwe pull /etc/hostname                      # or straight to stdout
dwe push ./probe.sh /tmp/probe.sh           # into the guest
echo "hello" | dwe push - /tmp/greeting     # from stdin
```

Transfers are binary-safe and whole-file. Encoding is handled inside the protocol, so you never have to improvise `base64` through a shell pipeline to get a binary out intact.

## Work that outlives the connection

This is the part that makes a long investigation possible. `--detach` returns a job handle immediately, and the job keeps running when the connection closes:

```console
$ dwe exec --detach -- make -C /src world
1
```

Come back whenever — a minute later, an hour later, over as many separate connections as you like:

```console
$ dwe jobs
1      running      make -C /src world

$ dwe output 1
[... everything so far ...]

$ dwe output 1 --follow          # or watch it live
$ dwe signal 1 15                # or stop it
```

### Reading only what is new

Polling a job repeatedly with plain `dwe output` re-reads everything from the start. To pick up where you left off, ask for the offsets and pass them back:

```console
$ dwe output 1 --offsets
[... output ...]
--since-stdout 4096 --since-stderr 128

$ dwe output 1 --since-stdout 4096 --since-stderr 128
[... only what arrived since ...]
```

The cursor is yours to keep rather than something `dwed` tracks. It has no sessions and cannot tell two callers apart, so a server-side cursor would have two people polling the same job eating each other's output.

> [!IMPORTANT]
> Job state lives in memory. A restart of `dwed` restores the listener but loses every job and everything it had captured. Output is capped at 16 MiB per stream, after which the tail is dropped and the reply says so — pipe a genuinely large job to a file in the guest and `pull` it instead.

## When it does not answer

**`cannot reach vsock:3:4820`** — the machine is not running, has no vsock device, or is using a different context id. Check the QEMU command line for `vhost-vsock-pci`.

**The connection opens but nothing answers** — `dwed` is not running in the guest. Its service definition was shipped but never applied: an image has to name `dwed-service.reg` in `[registry] autoapply` for anything to start. On the console, look for `peinit: service dwed started`.

**`protocol mismatch`** — `dwe` and `dwed` are from different builds. The wire version is checked rather than guessed at, so this is reported instead of being allowed to misparse. Rebuild both.

**Nothing at all, and the machine is wedged** — `dwed` goes down with the machine it is debugging. Below that line the serial console is still the tool.

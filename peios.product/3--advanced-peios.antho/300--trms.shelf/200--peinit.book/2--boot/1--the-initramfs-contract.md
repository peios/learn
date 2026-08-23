---
title: The Initramfs Contract
description: peinit starts with the root already assembled — what the handoff guarantees, and everything that stays outside it.
---

peinit starts with the root filesystem already assembled. Everything
that makes a root mountable — LUKS decryption, LVM activation, RAID
assembly, any filesystem check — belongs to the initramfs and has
happened before peinit exists. peinit performs no root assembly, no
decryption, no repair, and no fsck, and it does not assume one has been
done.

## The handoff

The initramfs transfers control by `chroot`-ing into the assembled root
and exec'ing peinit there. Not `switch_root`, and not `pivot_root`: the
kernel refuses to relocate onto the initramfs rootfs, so that route is
closed. The consequence is that the initramfs rootfs does not go away.
It remains the mount-namespace root — emptied, and unreachable from
peinit's view, but present. peinit therefore never assumes a clean
single-root mount topology, and never attempts `pivot_root`.

peinit is installed in package storage at `/usr/bin/peinit2` and reached
through the fixed runtime path `/bin/peinit2`. The boot-image tooling
sets the kernel `init=` to the runtime path. Before the transfer, the
initramfs has assembled the base StrataFS topology, including the `/bin`
and `/sbin` views, because peinit reaches every binary it execs through
them.

At handoff:

- the real root is mounted **read-write** at `/`;
- `/proc`, `/sys` and `/dev` are mounted and have been moved into the
  real root;
- the environment holds `TERM` and nothing else, and argv is just
  peinit's own path.

The read-write requirement is registryd's, not peinit's. loregd's
storage backend needs to write its write-ahead log and shared-memory
files even to answer a read, so a read-only root cannot support Phase 2
at all. Delivering the root writable is the initramfs's job; peinit only
confirms it.

peinit inherits nothing from that environment. It does not rely on
having been given anything, and it does not pass its own near-empty
startup environment through to services — the environment a service
receives is constructed from scratch (§5.5).

## What stays outside

Non-root storage is not peinit's concern. Data partitions and additional
filesystems are mounted at the services layer, typically by a Oneshot
service that runs `mount`. peinit has no mount feature beyond the fixed
Phase 1 set.

> [!NOTE]
> The initramfs itself is assembled by mkirf from hook scripts that
> packages contribute; mkirf resolves the ordering and bakes the
> sequence its PID 1 runs. What peinit depends on is the handoff
> contract above, not how the initramfs arranged to satisfy it.

---
title: Install Destinations
description: The /usr layout a package installs into, why package storage under /usr is kept apart from the root-level views, and where the boot paths are.
---

Peios separates package storage under `/usr` from the root-level views,
such as `/bin`, `/lib` and `/etc`, that software reads. The views are
assembled by the boot and base-filesystem layers from `/usr` and the
machine's own trees; they are not package storage. A package holds paths
under `/usr` only (§5.13), and the views show them at their usual places.

## The layout

A package SHOULD install into these destinations, and only these:

| Path | Purpose |
|---|---|
| `/usr/bin/` | Programs a person runs, administrative ones included |
| `/usr/sbin/` | System programs: daemons, init, boot, and service executables |
| `/usr/lib/<triplet>/` | Architecture-specific libraries and data (§5.15) |
| `/usr/lib/debug/` | Separated debug information, at the paths of the files it describes |
| `/usr/lib/modules/` | The closure's kernel, `vmlinuz`, and its modules, one kernel per closure |
| `/usr/lib/firmware/` | Device firmware, by device |
| `/usr/lib/earlyirf/<segment>/` | What the kernel reads from the initramfs before the rest (below) |
| `/usr/lib/os-release` | The operating system's identity |
| `/usr/libexec/` | Programs other programs run |
| `/usr/libexec/prelude/hooks.d/` | Initramfs boot hooks |
| `/usr/share/` | Architecture-independent data |
| `/usr/include/` | Headers |
| `/usr/src/debug/` | Debugger source, as the build's source tree |
| `/usr/src/dist/` | Corresponding source |
| `/usr/etc/` | Default configuration for software that reads `/etc` |
| `/usr/conf/` | Defaults for native software's supplementary configuration |

This version doesn't enforce the layout: a consumer composes whatever paths
a package holds.

## Notes on individual destinations

`/usr/etc/` is the bottom layer of the `/etc` view, which also merges the
machine's reconciled `/system/retc` and its own `/lcl/etc`, in that order. A
package never writes `/etc` itself. `/usr/conf/` is the bottom layer of
`/conf`, beneath `/lcl/conf`.

`/usr/lib/modules/` holds one kernel, `vmlinuz`, and its modules, directly:
there is no directory for each kernel release, because a closure holds one
kernel.

`/usr/lib/earlyirf/` matters only in an initramfs. Each directory in it is
a segment, whose contents map onto the root of the uncompressed archive the
kernel reads first, such as
`/usr/lib/earlyirf/intel-ucode/kernel/x86/microcode/GenuineIntel.bin`. An
administrator's segment of the same name in `/lcl/lib/earlyirf/` replaces
it. `/usr/libexec/prelude/hooks.d/` is likewise read by the initramfs
builder, with `/lcl/libexec/prelude/hooks.d/` before it.

What a root holds outside `/usr`, its mountpoints and links, is its root
skeleton file's (PSPU book 11), which a package such as the base filesystem
ships at `/usr/share/skeleton`.

> [!NOTE]
> What a package doesn't install into, and why:
>
> - `/bin`, `/sbin`, `/lib`, `/libexec`, `/share`, `/include`, `/etc` and
>   `/conf` are **views**, computed from the trees beneath them.
> - `/lcl` is the **machine's own** tree, which survives reinstalling.
>   `/lcl/policy` holds inputs that grant authority.
> - `/system` is **derived**: from the image, the registry or the platform.
> - `/var` is state a running system makes; a package's service makes its
>   own state directories.
> - `/opt`, `/srv`, `/home`, `/media` and `/mnt` belong to the operator and
>   users, and `/dev`, `/proc`, `/sys`, `/run` and `/tmp` to the running
>   system.
> - `/usr/local` doesn't exist: `/usr` is never written by anything but
>   packages, and `/lcl` is the machine's.

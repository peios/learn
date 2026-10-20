---
title: Install Destinations
description: The permitted top-level destinations, why package-owned storage under /usr is separate from the root-level runtime views, and the drop-in directories.
---

Peios separates package-owned vendor storage under `/usr` from the
root-level runtime views such as `/bin`, `/lib`, and `/sbin`. Those
views are filesystem topology assembled by the boot and base-filesystem
layers; they are not package storage. A package installs its files under
`/usr`, and the runtime topology projects them at their canonical paths.

Within `/usr`, executables split by kind. `/usr/sbin/` holds **system
binaries** — daemons, init and boot binaries, and service executables
not normally invoked directly by a person. `/usr/bin/` holds everything
else, including administrative tools a person does invoke directly, even
those requiring administrator privileges.

## Permitted top-level destinations

| Path | Purpose |
|---|---|
| `/usr/bin/` | Executables that are not system binaries — user-facing tools, and admin tools invoked directly |
| `/usr/sbin/` | System binaries — daemons, init and boot binaries, service executables |
| `/usr/lib/<triplet>/` | Architecture-specific libraries and arch-dependent data (§5.15) |
| `/usr/lib/debug/` | Separated debug information, mirroring the install paths of the files it describes |
| `/usr/lib/modules/<release>/` | Kernel content for one kernel release: its modules, and the kernel image, `System.map`, and build config alongside them |
| `/usr/lib/firmware/` | Device firmware blobs, addressed by device rather than by host triplet |
| `/usr/lib/os-release` | The freedesktop OS-identity file, at a fixed external contract path |
| `/usr/libexec/` | Architecture-independent helper executables run by another program rather than by a person |
| `/usr/share/` | Architecture-independent data |
| `/usr/include/` | Header files |
| `/usr/src/debug/` | Debugger source files, mirroring the build's source tree |
| `/usr/src/dist/` | Corresponding source shipped by `-source` packages |
| `/usr/etc/` | Vendor-shipped default configuration for legacy applications — the bottom layer of the `/etc` merge |
| `/usr/conf/` | Vendor-shipped defaults for the supplementary configuration of native applications — the bottom layer of the `/conf` merge |
| `/var/` | Runtime variable state directories, empty at install time |
| `/boot/` | `/boot/initramfs/`, a complete independent root filesystem, and `/boot/efi/`, the EFI System Partition |
| `/hooks/` | Initramfs boot hooks, discovered and ordered when the initramfs cpio is packed |
| `/++/` | Initramfs early-cpio segments, prepended uncompressed ahead of the main archive |

A payload entry MUST NOT install under any other top-level path, unless
the package declares itself a special system package (below).

A consumer MUST enforce this at install time. Producer-side validation
proves nothing about a package file that arrives from elsewhere.

## Notes on individual destinations

Only the `debug/` and `dist/` subtrees of `/usr/src/` are permitted; the
rest of `/usr/src/` is administrator territory.

`/usr/etc/` is where package configuration goes. A package never writes
`/etc` directly, because `/etc` is a merged view resolving
`/usr/etc` < `/system/retc` < `/lcl/etc`, not storage. `/usr/conf/` is
the equivalent bottom layer of the `/conf` merge (`/usr/conf` <
`/lcl/conf`); native software reads the registry directly, so there is
no reconciled layer between them.

`/var/` accepts **empty directories only**, establishing locations a
runtime will write to — `/var/log/<service>/`, `/var/state/<service>/`.
Populated content under `/var/` is invalid: variable state is owned by
the runtime, not by the package.

`/hooks/` is meaningful only in an initramfs root, where the cpio packer
scans it. In an ordinary system root it is an unused permitted
destination.

An entry under `/boot/` SHOULD be a symlink whose target resolves to a
regular file under one of the other permitted destinations — typically
`/usr/lib/<triplet>/` for a kernel image, initramfs, or device tree.
`/boot/` is a discovery directory a bootloader reads, not storage where
real package content lives. This is a SHOULD rather than a MUST because
recovery images and embedded bootloader integrations that cannot follow
symlinks exist; a format-level validator does not enforce it.

A package reaching `/boot/initramfs/` is cross-targeting a different
root, not installing into this one (§5.19).

> [!NOTE]
> What is absent from the list, and why:
>
> - `/bin`, `/sbin`, `/lib`, `/lib64`, `/libexec`, `/share`, `/include`,
>   `/etc`, `/conf` — **merged views**, computed from the trees beneath
>   them so that software sees one path while authority stays separated.
>   A package writes the `/usr` layer and the view does the rest.
> - `/lcl` — the **operator's** tree, the peer to `/usr` that is backed
>   up and survives reinstall. `/lcl/policy` in particular holds inputs
>   that grant authority; writing there yields arbitrary code at boot,
>   which is why packages are excluded structurally rather than by rule.
> - `/system` — **derived** from the image, registry, or platform, and
>   always reconstructible.
> - `/opt` — **operator territory**, deliberately off the list. Software
>   there brings its own layout, is invisible to package verification,
>   and participates in none of these guarantees.
> - `/dev`, `/proc`, `/sys`, `/run`, `/tmp` — kernel interfaces and
>   runtime-only directories; not storage a package can populate, not
>   even as empty directories.
> - `/srv`, `/data`, `/home`, `/media`, `/mnt` — operator and user
>   namespaces.
> - `/usr/local` — does not exist. `/usr` is meant to be untouchable,
>   and a writable subdirectory of it makes that a lie; `/lcl` is the
>   honest version.
> - `/root` — does not exist. There is no root.

## Special system packages

A few packages exist precisely to lay down the structure these rules
protect — the base-filesystem package that mints the runtime mountpoint
tree is the archetype. For those, the allowlist is not a guardrail but
the thing being installed.

Such a package MAY set `special_system_package` in its manifest
(§5.18). The declaration waives the layout checks **at production time
only**. It grants nothing at install time: a consumer MUST refuse an
out-of-layout payload unless the operator has *also* explicitly opted
in, through a distinct and deliberate act naming that intent.

This is two keys held by two parties. A package may propose its own
exemption; only whoever installs it can grant one.

When a consumer meets the declaration without having been given the
opt-in, it MUST refuse the package with an error **naming the refused
request**, so that an operator can tell "this package asked for an
exemption I did not grant" from "this package is malformed".

`/lcl/policy` MUST NOT be reachable by this route under any
circumstance. It is the tree whose contents grant authority, and an
exemption that could reach it would convert a structural guarantee into
a policy one.

## Drop-in directories

Several subdirectories of the `/etc` merge are **drop-in directories**:
their contents are interpreted as code or configuration by other tools,
notably the side-effect tools of §5.24 and system daemons that read
configuration drop-ins. A package writing into one has indirect
influence on the behaviour of components that read it.

A package from a repository other than the system's official repository
MUST NOT install a file at the top level of the `/usr/etc` layer of any
of these:

- `ld.so.conf.d/`
- `profile.d/`
- `sudoers.d/`
- `cron.d/`, `cron.daily/`, `cron.hourly/`, `cron.weekly/`,
  `cron.monthly/`
- `sysctl.d/`
- `modules-load.d/`
- `modprobe.d/`
- `binfmt.d/`
- any directory the system declares as a drop-in directory through its
  configured list

The consumer's drop-in directory list MUST be stored under a security
descriptor granting write access only to a recovery-class operator
principal, never to the principal performing installs. Operator
configuration MAY add entries to the list but MUST NOT remove an entry
this specification requires: the list is purely additive.

A non-official-repository package whose payload installs to one of those
paths MUST be rejected at install time.

A non-official-repository package MAY install drop-in files under its
own subdirectory of a drop-in path — for example
`/usr/etc/ld.so.conf.d/<repo-name>/<package>.conf` — provided the
subdirectory is namespaced by both the repository's name and the
package's name, so that two such packages cannot collide.

> [!NOTE]
> The restriction closes a concrete chain. A low-trust repository
> installs a configuration file at the top level of `ld.so.conf.d/` that
> extends the loader's library search path. At the next transaction that
> declares `ldconfig` — from any repository, not necessarily the same
> one — the drop-in is honoured and the loader's behaviour changes.
> Restricting top-level drop-in writes to the official repository, with
> a namespaced escape hatch for legitimate non-official content, breaks
> the chain without forbidding the use case.

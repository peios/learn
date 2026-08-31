---
title: Quick start
type: how-to
description: Build the Experimental medium from a four-line spec and boot it under QEMU — no root, one command.
related:
  - peios/peiso/building-images/overview
  - peios/peiso/building-images/running-a-build
  - peios/peiso/reference/the-spec
---

This page builds the Peios Experimental medium and boots it. It assumes a checkout of the Peios tree with a populated package pool (`pkgs/_pkgsOut_`), which is where the edition and its closure come from today.

## What you need on the build host

- **peiso**, built from `peiso/` in the tree (`go build -o peiso .`), or on your PATH.
- **squashfs-tools**, **xorriso**, **dosfstools** and **mtools** — the host-side packers. Everything Peios-specific (the initramfs and UKI tools) is taken from the root being built.
- For booting: **QEMU** with KVM and the **OVMF** firmware.

No root. If any step asks for it, that is a bug.

## The spec

`dist/release/experimental.toml`:

```toml
[[packages.repository]]
url = "file://../../pkgs/_pkgsOut_/"
keys = ["../../pkgs/dev-signing.pub"]

[baseline]
edition = "Experimental"
source_date = "2026-06-22T00:00:00Z"
```

That is the whole thing. The edition name is lowercased and hyphenated to find the package — `peios-experimental` — and, with no `version`, the newest one wins. `keys` names the public key the pool's packages were signed with; the medium repository has to trust it to carry them. [The spec](~peios/peiso/reference/the-spec) lists every key.

## Build

```sh
cd dist/release
peiso iso experimental.toml
```

peiso reports each stage:

```text
resolving peios-experimental
resolved peios-experimental 2026.8-1 (79 packages)
composing dist/peios-experimental-2026.8/root
resolving medium packages
publishing dist/peios-experimental-2026.8/repo
medium repo: 2 packages, trust anchor 6e50…
staged seed authd-policy
…
seeds: 15 staged
packing initramfs -> …/root/system/boot/initramfs.cpio.zst
squashing root -> …/rootfs.squashfs
squashed with 4414 signature attribute(s)
building UKI -> …/root/boot/efi/EFI/BOOT/BOOTX64.EFI
building ISO -> dist/peios-experimental-2026.8/peios-experimental-2026.8.iso
dist/peios-experimental-2026.8/peios-experimental-2026.8.iso
```

The last line is the ISO. Everything the build made is beside it, in `dist/peios-experimental-2026.8/` — see [Running a build](~peios/peiso/building-images/running-a-build) for the layout.

## Boot

```sh
make boot
```

runs QEMU with UEFI firmware, the ISO attached as a virtio disk, and the serial console on your terminal. You will see the kernel, then `prelude` (the initramfs PID 1) running its hooks — `live-boot` finds the medium and mounts the live root — then `peinit` bringing up the services the release's seeds define, and finally a login prompt. The image autologs in a development account.

The same Makefile has `boot-dwe`, `boot-install` and `boot-installed`; [Running a build](~peios/peiso/building-images/running-a-build) covers them.

## Change something

Two things are yours to change in the spec without touching anything else:

```toml
[devtools]
dwe = true            # a development medium; builds to …-2026.8-dwe/

[registry]
remove = ["lpsd-first-account"]   # drop a seed the release would apply
add    = ["my-service"]           # add one a package in the closure ships

[[package]]
name = "bash"                     # carry a package the edition does not
```

To change *what the release is*, change the edition package (`pkgs/peios-experimental/`) and republish it; the spec does not change. [Editions](~peios/peiso/editions-and-upgrades/editions) explains why that line is drawn where it is.

---
title: Quick start
type: how-to
description: Run your first peiso build — a minimal peiso.toml that composes the package root and packs the initramfs, and what it leaves on disk.
related:
  - peios/building-images/overview
  - peios/building-images/running-a-build
  - peios/peiso/reference/the-build-spec
  - peios/package-management/composing-a-root
---

This page runs the smallest build peiso can do. At the end you have a composed Peios package root on disk with the initramfs cpio packed inside it, produced by one `sudo peiso build` against a three-table `peiso.toml`. The squashfs, UKI, and ISO stages are opt-in and stay off here — see [The build pipeline](~peios/building-images/the-build-pipeline) for the full chain.

## Prerequisites

peiso orchestrates other tools and composes real packages, so all three of these are hard requirements — there is no build without them.

- **Root.** The build chroots into the composed root to run its shipped applets, so it must run as root. Run it under `sudo`.
- **`peipkg-compose` on `PATH`.** peiso shells out to it to compose the root. If it is installed somewhere `sudo` cannot see, set `PEISO_COMPOSE` to its path — the full lookup chain is in [Running a build](~peios/building-images/running-a-build#environment).
- **A package source.** peiso does not fetch or build packages. You need built `.peipkg` files (a package farm) and a **multi-root compose manifest** that lays them out: it must produce both the main root and a nested initramfs root, and the packages it installs must include `peiosutils` (which ships the `mkirf` applet the build runs inside the root) and `fsbase` (which owns the `/system/boot` directory the cpio is written into). The Peios repository's `dist/prod/manifest.toml` is the reference manifest, composed from the repository's own farm; writing manifests is covered in [Composing a root](~peios/package-management/composing-a-root).

No other host tools are needed for this build. `mksquashfs`, `xorriso`, and friends only come into play when you enable the optional stages.

## Lay out the build directory

Work in a directory that holds your compose manifest. With the reference setup that is the repository's `dist/prod/` directory, which already contains a full `peiso.toml`; to follow this page from scratch, use a fresh directory containing:

- `manifest.toml` — your multi-root compose manifest;
- the package farm it references via its `local_packages` globs;
- `peiso.toml` — written in the next step.

## Write the minimal spec

Create `peiso.toml` next to the manifest:

```toml
schema = 1

[root]
manifest = "manifest.toml"
out      = "root"

[initramfs]
dir  = "boot/initramfs"
cpio = "system/boot/initramfs.cpio.gz"
```

This is the whole spec — `schema`, `[root]`, and `[initramfs]` are the only required tables. `manifest` and `out` are resolved relative to the spec file's own directory, so the build behaves the same wherever you invoke it from. `dir` and `cpio` are relative to the composed root: `dir` names the nested initramfs root your multi-root manifest produces, and `cpio` is where `mkirf` writes the packed archive inside the root. Every field, including the optional ones this spec omits, is documented in [The build spec](~peios/peiso/reference/the-build-spec).

## Run the build

```bash
cd /path/to/your/build/dir
sudo peiso build
```

`build` takes one optional argument, the spec path, and it defaults to `peiso.toml` in the current directory — so the bare command above is enough. peiso prints one progress line per stage, with your absolute paths substituted:

```
peiso: composing root -> /path/to/your/build/dir/root
peiso: packing initramfs (chroot /path/to/your/build/dir/root) -> /system/boot/initramfs.cpio.gz
peiso: built /path/to/your/build/dir/root
```

`peipkg-compose`'s own output streams between the first two lines. On a rebuild, a `peiso: cleaning …` line appears first: peiso deletes the previous `root/` and composes fresh every time, so never keep anything you care about inside it. The command exits `0` on success.

If it fails, the error is printed as `peiso: <err>` and the exit code is `1`. The three you are most likely to hit first:

- `build chroots into the composed root and must run as root (try: sudo peiso build)` — you forgot `sudo`.
- `peipkg-compose not found on PATH or next to peiso (set PEISO_COMPOSE to override)` — see the [environment section of Running a build](~peios/building-images/running-a-build#environment); `sudo`'s `secure_path` is the usual culprit.
- `/usr/bin/mkirf not in the composed root … (is peiosutils composed in?)` — your manifest did not compose `peiosutils` in, so the root has no `mkirf` to pack the initramfs with.

## What landed on disk

The build leaves one artifact tree, rooted at the spec's `out` directory:

- `root/` — a complete, valid peipkg package root: every package's files at their installed paths, plus a seeded peipkg state database.
- `root/boot/initramfs/` — the nested initramfs root, composed in the same pass by the multi-root manifest.
- `root/system/boot/initramfs.cpio.gz` — the packed initramfs cpio, exactly where an installed system stores its own.

Confirm the cpio exists:

```bash
ls -lh root/system/boot/
```

There is no rootfs squashfs, no UKI, and no `peios.iso` — those stages only run when their spec tables are present, and this spec left them out.

## Where to go next

- **Understand what just ran.** [The build pipeline](~peios/building-images/the-build-pipeline) walks every stage in order — the compose, the chroot, and the optional stages this build skipped.
- **The command in full.** [Running a build](~peios/building-images/running-a-build) covers the exit codes, host-tool checklist, environment, and the `dist/prod/` Makefile workflow that drives real builds.
- **Grow the spec.** Add `[squashfs]`, `[uki]`, and `[iso]` tables to carry this build all the way to a bootable live ISO — every field is in [The build spec](~peios/peiso/reference/the-build-spec).

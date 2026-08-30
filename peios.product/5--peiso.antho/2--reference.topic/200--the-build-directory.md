---
title: The build directory
type: reference
description: What a peiso build leaves in dist/peios-<edition>-<version>/ — root, repo, sidecars, squashfs, UKI, ISO, and the compose manifest and lock that record what was resolved.
related:
  - peios/peiso/building-images/the-build-pipeline
  - peios/peiso/building-images/running-a-build
---

Every build writes to one directory, named for what was resolved: `dist/peios-<edition>-<version>/`, with `-dwe` appended for a development medium. The version is the edition package's without its packaging revision — `2026.8`, not `2026.8-1`. The directory is relative to where peiso is run; `peiso root --out` overrides the root's location only.

A build refuses to run if `root/` already exists. Remove the directory (or `make clean`) to rebuild.

| Entry | Written by | |
|---|---|---|
| `compose.toml` | compose stage | The generated compose manifest: sources, the `initramfs` root, the edition and extra package requests. Marked "do not edit". |
| `compose.lock.toml` | compose stage | The resolved closure: every package, version, root, source and hash. What the image *is*, exactly. |
| `root/` | compose stage | The composed system. `root/boot/initramfs/` is the initramfs root; `root/var/state/peipkg/` its database; `root/lcl/conf/peipkg/` its repository configuration. |
| `sidecars.jsonl` | compose stage | The signature sidecars compose recorded instead of stamping: one `{path, blob}` per line, path relative to `root/`. Consumed by the squashfs stage. |
| `customisations.toml` | customise stage | Every file, autorun and feature the spec added, with the host paths they came from. |
| `repo/` | medium stage | The medium repository: descriptor, indexes, keys, and the `disk-boot` packages. Copied onto the ISO as `repo/`. |
| `root/lcl/conf/peipkg/peios-medium.repo` | medium stage | The client configuration for it, anchored on this build's key. |
| `root/lcl/policy/autoapply.d/*.reg` | seeds stage | The staged seeds. |
| `root/lcl/policy/autorun.d/10-apply-seeds.sh` | seeds stage | The autorun that drains them at boot. |
| `root/system/boot/initramfs.cpio.gz` | initramfs stage | The packed initramfs, inside the root. |
| `rootfs.squashfs` | squashfs stage | The live root filesystem, with signature attributes. Outside `root/` so it cannot contain itself. |
| `root/boot/efi/EFI/BOOT/BOOTX64.EFI` | UKI stage | The unified kernel image. `root/boot/efi/` is the ESP tree. |
| `peios-<edition>-<version>[-dwe].iso` | ISO stage | The medium. |

The Makefile adds its own files beside the spec, not in the build directory: `disk.img` (the install target), `ovmf-vars.fd` (firmware variables, reset on every boot), and `console.log` from `drive.py`.

Only the ISO is needed to boot or install. `root/` and `rootfs.squashfs` are kept because they are what you look at when something is wrong; `compose.lock.toml` is kept because it is the provenance.

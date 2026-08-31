---
title: The build pipeline
type: concept
description: Every stage of a peiso build in order — resolve and compose, the medium repository, registry seeds, initramfs, squashfs with signature attributes, UKI, ISO — and what each one leaves behind.
related:
  - peios/peiso/building-images/overview
  - peios/peiso/reference/the-build-directory
  - peios/package-management/composing-a-root
  - peios/boot-and-trust-establishment/mkirf
  - peios/boot-and-trust-establishment/mkuki
---

`peiso iso` runs seven stages. `peiso root` runs only the first. Each stage consumes what earlier ones produced, and everything lands in one build directory, `dist/peios-<edition>-<version>[-dwe]/` — [The build directory](~peios/peiso/reference/the-build-directory) lists its contents.

## 1. Resolve and compose the root

peiso writes a [compose manifest](~peios/package-management/composing-a-root) naming the edition package (at the spec's `version`, or any), the medium's extras (`live-boot` for `first_boot = "live"`, none at all for `"none"`; `peios-dwe` when `dwe = true`), the spec's package sources, and one named root, `initramfs` at `boot/initramfs`.

A `file://` source that holds a repository descriptor is declared as a repository; one that does not (the local pool, `pkgs/_pkgsOut_`) joins as local packages. Then peiso resolves — a lock — and reads the edition's resolved version from it, because the build directory is named after that version and the spec may not have said it. Only then does it compose, from the lock, into `root/`. The manifest and lock are kept beside the root: they record exactly what was resolved.

Two things about the composed tree:

- **It is complete but attribute-less.** Where a package carries a signature sidecar for a non-ELF file (device firmware: `<file>.peios.sig`), compose would normally set the target's `security.peios.sig` attribute — which needs `CAP_SYS_ADMIN`. peiso asks compose to *record* each one instead (`sidecars.jsonl`), and writes them into the squashfs at stage 5. The `root/` on the build host therefore carries no security attributes; the image does.
- **The initramfs is a second root inside it.** Packages the initramfs runs — `prelude`, its hooks, the module subset — are placed there by the edition's cross-root dependency edges, not by anything peiso does.

Compose is given the composer's half of the Special System Package exemption: `fsbase` lays down the mountpoint tree the layout rules otherwise protect, and a root with no `/proc` is not a root.

## 2. Publish the medium repository

The installer swaps the live boot packages for the disk ones on the target, and it takes `disk-boot` and `disk-boot-irf` from a repository carried on the medium — a live image cannot carry them installed, because `live-boot-irf` and `disk-boot-irf` conflict in the initramfs.

peiso resolves those two packages against the same source scan the root's lock came from — not merely the same source declarations, the same gathered universe, so a package republished mid-build cannot give the root and the medium different revisions. It publishes them into `repo/` with a key generated for this build, and writes `root/lcl/conf/peipkg/peios-medium.repo` naming that key as the trust anchor and `file:///media/peios/repo` as the base URL — where `live-boot` mounts the medium.

The key is a throwaway and its private half is never written anywhere. A key shipped beside the repository it signs proves nothing about it — tampering with the ISO tampers with both — so its only job is to satisfy the "required" signature policy that peipkg rightly insists on. The repository's descriptor also lists the keys the *packages* were signed with (`keys` in the spec): a repository accepts a package only if its signer is in the descriptor.

## 3. Stage the registry seeds

Packages ship registry seed masters under `/usr/share/regim/`, and installing a package applies none of them: which seeds a system runs is policy, not payload. The edition states that policy in `/usr/share/peios/release.toml`. peiso reads it from the composed root, applies the spec's `[registry] add` and `remove`, adds `dwed-service` for a DWE medium, and copies each named seed into `root/lcl/policy/autoapply.d/`. It also places the autorun script that drains that queue — `reg apply --dir /lcl/policy/autoapply.d --once-delete` — which peinit runs at boot before it plans its services, so the services the seeds define start on the very boot that creates them.

A seed the spec names that no package in the root ships is an error, not a warning.

## 4. Pack the initramfs

[`mkirf`](~peios/boot-and-trust-establishment/mkirf) packs `root/boot/initramfs/` into `root/system/boot/initramfs.cpio.gz` — inside the root, where an installed system keeps its own, so the squashfs carries it. Two subtrees are excluded: `var/state/peipkg` (the initramfs root's package database) and `lcl/conf/peipkg` (its repository configuration). Both belong to the real root.

mkirf is the copy in the root being built, run on the host under the root's own dynamic loader (`usr/lib/<triplet>/ld-linux-*.so.2 --library-path … --argv0 mkirf …/usr/bin/peiosutils`). No chroot, no privilege, and no second implementation of the tool the running system uses.

## 5. Squash the root

The whole `root/` becomes `rootfs.squashfs` (zstd). peiso streams the tree to `mksquashfs -tar` as a PAX tar rather than pointing it at the directory, for three reasons that all come down to the same property — the image is what a privileged build would have produced:

- every entry is `root:root`, though the build user owns the files on disk;
- every recorded signature from stage 1 becomes the file's `security.peios.sig` attribute, written into the squashfs by name — a squashfs stores whatever attributes the tar names;
- every mtime is the spec's `source_date`, and entries are emitted in sorted order, so the image is reproducible.

A recorded signature whose file is not in the root is an error: a stale record must not ship unsigned firmware.

## 6. Build the UKI

[`mkuki`](~peios/boot-and-trust-establishment/mkuki) — again the shipped copy, run the same way — bundles the kernel from `root/usr/lib/modules/<release>/`, the cpio from stage 4, and the command line `live-boot` ships (`root/usr/share/live-boot/cmdline`) into one EFI binary at `root/boot/efi/EFI/BOOT/BOOTX64.EFI`. It runs after the squashfs so the image does not carry the ESP tree.

## 7. Author the ISO

`root/boot/efi/` becomes a FAT32 image (`mkfs.vfat` + `mcopy`, no mount), which `xorriso` appends to the ISO as a GPT EFI System Partition. The ISO's data area carries `rootfs.squashfs` and `repo/`. The result is `peios-<edition>-<version>[-dwe].iso`, label `PEIOS`, which UEFI firmware boots directly: the UKI's initramfs runs `live-boot`, which finds the medium by that label, mounts the squashfs over an overlay, and pivots.

## What each stage needs

| Stage | Runs | From |
|---|---|---|
| compose | peipkg's compose library | in-process |
| medium repository | peipkg's repopub library | in-process |
| seeds | file copies | in-process |
| initramfs | `mkirf` | the root, via its loader |
| squashfs | `mksquashfs` | build host |
| UKI | `mkuki` | the root, via its loader |
| ISO | `mkfs.vfat`, `mcopy`, `xorriso` | build host |

Nothing runs as root, and nothing runs inside the root.

---
title: The build pipeline
type: concept
description: "Each stage of a peiso build in order, from compose to ISO — which stages run host tools, which run Peios applets in the chroot, and why the order matters."
related:
  - peiso/building-images/overview
  - peiso/reference/the-build-spec
  - peios/package-management/composing-a-root
  - peios/boot-and-trust-establishment/mkirf
  - peios/boot-and-trust-establishment/mkuki
---

A single `sudo peiso build <spec>` turns one declarative [build spec](~peiso/reference/the-build-spec) into a bootable image. It does this by running a fixed, ordered sequence of **stages** — compose the root, pack the initramfs, stage first-boot state, squash the rootfs, bundle a UKI, author an ISO. This page walks each stage in the order peiso runs them and explains why that order is what it is.

## Two core ideas

Everything here rests on two ideas that are worth holding in mind before the stage-by-stage walk.

**Compose does the packages; peiso does the boot machinery.** peiso does not know how to resolve a package set or lay out a root — that is [`peipkg-compose`](~peios/package-management/composing-a-root)'s job, and peiso simply shells out to it. What peiso adds is everything compose [deliberately does not do](~peios/package-management/composing-a-root): pack the initramfs, seed first-boot registry and feature state, produce a rootfs image, bundle a Unified Kernel Image, and author a bootable ISO. The line is clean: compose stops at *here is a valid peipkg root*, and peiso begins there.

**The chroot model lets peiso run Peios-native applets against the composed root.** Several stages are not host tools at all — they are Peios boot applets (`mkirf`, `mkuki`) that ship *inside* the composed root, at `/usr/bin/mkirf` and `/usr/bin/mkuki`. peiso `chroot`s into the composed root and runs them there, so they operate on the tree exactly as they would on a live, booted system. This is why the build is privileged, and why the applets take root-relative paths. peiso never carries its own copy of these tools; it uses the ones the image was composed with.

Determinism runs through the whole pipeline. The spec's `source_date` is threaded into every build-stamped timestamp — compose derives its output stamps from it, and peiso pins the squashfs timestamps from it — so the same spec, manifest, lock, and packages yield a byte-reproducible image.

## The stages, in order

The stages below are the exact sequence of `build.Run`. Optional stages (marked *optional*) run only when their spec section is present.

### 1. Preconditions

peiso **must run as root** (effective UID 0), because it `chroot`s — it checks this first, and the failure message and full rationale are covered in [Running a build](~peiso/building-images/running-a-build).

It then locates the `peipkg-compose` binary. The search order is: the `PEISO_COMPOSE` environment variable (overrides everything), else the binary on `PATH`, else a **sibling of the peiso binary itself** — the two are installed together, and `sudo`'s `secure_path` routinely drops the directory (e.g. a Go `GOBIN`) where the sibling sits, so peiso looks right next to itself as a fallback.

### 2. Clean the output root

> [!WARNING]
> peiso `RemoveAll`s the prior `[root].out` directory — a recursive delete running as root. This is necessary because `peipkg-compose` **refuses to write into an existing directory** — its build is atomic, so the output is either absent or a complete root. peiso owns `root/` as a rebuildable artifact, so it clears it for a clean rebuild. Because a stray recursive delete running as root is costly, the clean is guarded: it refuses obviously unsafe targets (empty, `.`, the filesystem root, or any path whose parent is itself). This single clean also clears the nested initramfs root underneath.

### 3. Compose the main root

peiso shells out to the package stage:

```
peipkg-compose build <[root].manifest> --update --out <[root].out>
```

This is where all package resolution and layout happens — see [Composing a root](~peios/package-management/composing-a-root). `--update` always re-resolves, so a stale `manifest.lock.toml` (left after editing the manifest or republishing a package) never blocks the build with a digest mismatch; peiso rebuilds against the current manifest and farm.

In the normal v1 setup the manifest is **multi-root**: one compose produces both the main system root at `[root].out` and the nested [initramfs root](~peios/package-management/named-roots) at `<out>/boot/initramfs` in the same pass. That single tree is why peiso needs none of the live consumer's cross-root transaction machinery here.

### 4. Compose a separate initramfs root — legacy, normally skipped

peiso composes the initramfs root as its *own* root **only if `[initramfs].manifest` is set**:

```
peipkg-compose build <[initramfs].manifest> --update --out <[root].out>/<[initramfs].dir>
```

This is the older, pre-multi-root form. With a multi-root main manifest the initramfs root is already nested in place from stage 3, so this stage is skipped. Treat `[initramfs].manifest` as **legacy**; new specs leave it unset and rely on the multi-root manifest.

### 5. Inject files into the initramfs root — temporary

If `[initramfs].inject` has entries, peiso copies each `src` file straight into the initramfs root at `dest`, forcing the declared `mode` (a `chmod` after write, so the executable bit survives `umask` — the initramfs prelude execs hooks via their shebang and they must stay executable in the cpio). If a `mode` is omitted the source file's permission bits are preserved.

This is a **temporary bypass of packaging**: it drops files (historically the live-boot root-mount hook) into the tree without a package owning them. It is explicitly transitional — the live-boot hook, for instance, is now packaged (`live-boot-irf` ships it and a cross-root dependency pulls it into the initramfs root during compose), so `inject` is expected to fall away as more of this content moves into packages.

### 6. Pack the initramfs

peiso chroots in and runs the composed root's own `mkirf`:

```
chroot <[root].out> /usr/bin/mkirf [--exclude <GLOB>]... /<[initramfs].dir> /<[initramfs].cpio>
```

This produces the gzip cpio (in the example spec, at `root/system/boot/initramfs.cpio.gz`) — the early-boot environment. The source and output paths are root-relative in the spec, so inside the chroot they are simply `/<dir>` and `/<cpio>`. `--exclude` globs keep things the early boot does not need out of the cpio (the peipkg database, for example). See [mkirf](~peios/boot-and-trust-establishment/mkirf) for what goes into the image and how it is assembled.

This runs **before** the squashfs (stage 9) deliberately, so the rootfs image contains this cpio — exactly as an installed system stores its initramfs under `/system/boot`. peiso does not mint that destination directory; the `fsbase` package, composed into the main root, owns it.

### 7. Stage registry seeds

If `[registry].autoapply` lists any seed masters, peiso copies each one from the composed root's vendor library at `/usr/share/peios/registry.d/` into the composer-owned queue at `/usr/system/share/autoapply.d/`, and drops a small autorun script (`10-apply-seeds.sh`) that drains the queue with `reg apply --once-delete` on boot. [peinit](~peios/peinit/overview) runs the script every boot; it is a no-op once the queue is empty.

The point of the two directories is curation: packages may drop seed *masters* into `/usr/share/peios/registry.d/`, but only peiso — the image — decides which of them auto-apply, by copying them into the `/usr/system` queue that packages are forbidden to write to. Nothing a package ships becomes boot-active unless this image listed it. This runs before the squashfs so the staged seeds ride into the rootfs image.

### 8. Stage features

If `[features].enable` lists any features, peiso writes a self-removing first-boot autorun script (`20-features.sh`, ordered after the seed-apply script) containing a `feat add <name>` line per entry. peinit runs it after [`registryd`](~peios/the-registry/lcs-and-sources) is up and **before** [Phase 2](~peios/peinit/boot-and-boot-modes) enumerates services, so the services a feature creates start the same boot.

The script removes itself after running (`rm -- "$0"`). On a persistent install that whiteout is durable, so it runs once. On the live read-only image the removal is an ephemeral tmpfs-overlay whiteout, so the script reappears and re-runs each boot — re-creating the services the fresh tmpfs registry would otherwise lose. As with the seeds, the *selection* lives in the image spec, not in any package: a package ships a feature's lifecycle scripts, but only the image turns it on.

### 9. Squashfs — optional

If `[squashfs]` is present, peiso squashes the **whole** composed root into a read-only rootfs image:

```
mksquashfs <[root].out> <tmp> -noappend -xattrs -mkfs-time <t> -inode-time <t> [-comp <compression>]
```

The timestamps `<t>` are fixed from `source_date` (falling back to epoch `0`) for reproducibility. `-noappend` forces a fresh image rather than appending to any existing one. `-xattrs` **preserves existing extended attributes** — KACS security descriptors ride in them — so the live rootfs carries the same security metadata an installed system would; it does not sign or add anything.

The image is written to a **temp path that is a sibling of the root, outside `root/`**, and renamed into `[squashfs].out` on success. Writing outside `root/` is what lets the squash be of the whole root with no excludes even when `out` itself lives inside the root tree: the growing output can never capture itself. (`src` and `out` must therefore share a filesystem, since the finalisation is a rename.) The result is byte-identical to an installed system — it even contains the initramfs cpio from stage 6.

### 10. UKI — optional

If `[uki]` is present, peiso chroots in and runs the composed root's `mkuki`:

```
chroot <[root].out> /usr/bin/mkuki --kernel /boot/vmlinuz-X --initramfs /<[initramfs].cpio> --cmdline "<text>" --out /<[uki].out>
```

This bundles the kernel (resolved from `/boot/vmlinuz-*` inside the root), the initramfs cpio from stage 6, and the kernel cmdline into a single EFI binary that UEFI firmware boots directly — no bootloader. The cmdline comes from `[uki].cmdline` if given, otherwise the trimmed contents of `[uki].cmdline_file` (read on the host and passed as a literal `--cmdline`, so the chroot needs no in-root file). Reading from the composed root's own cmdline file keeps build-time and runtime agreement — see [mkuki](~peios/boot-and-trust-establishment/mkuki). Like `mkirf`, `mkuki` is a Peios Dynamic-Boot applet, which is why it runs in the chroot against the tree that ships it.

### 11. ISO — optional

If `[iso]` is present, peiso authors a UEFI, USB/block-bootable ISO. This stage runs **on the host, not in the chroot** — `xorriso` is a build-host tool and the ISO is a host-side artifact, not a Peios boot tool.

peiso builds a FAT32 ESP image from the ESP tree at `[iso].source` (sizing a zero-filled file, formatting it with `mkfs.vfat -F 32`, and populating it with `mcopy` — no mount, no loop device), then has `xorriso` **append** that image as a GPT ESP partition (type `0xEF`). Firmware treats the `.iso` as a disk, reads the GPT, and boots the ESP's UKI at `[iso].efi_boot`. If a squashfs was built, it is placed into the ISO9660 data area (hard-linked when it shares a filesystem, so a multi-GB image is never duplicated) as a file the live system's mount-root hook reads off the medium by volume label — keeping the whole OS off RAM. The path is UEFI-only and USB/block by design; there is no BIOS/isolinux/El-Torito optical path relied on.

## External tools

peiso is an orchestrator: the heavy lifting is done by tools it shells out to. Some run on the build host; the Peios boot applets run *inside* the chroot against the composed root.

| Tool | Where it runs | Stage | Role |
|---|---|---|---|
| `peipkg-compose` | host | 3, 4 | Resolve and lay out the package-owned root(s). |
| `chroot` → `/usr/bin/mkirf` | inside the chroot | 6 | Pack the initramfs cpio (Peios applet shipped in the root). |
| `mksquashfs` | host | 9 | Build the read-only rootfs image. |
| `chroot` → `/usr/bin/mkuki` | inside the chroot | 10 | Bundle the UKI (Peios applet shipped in the root). |
| `xorriso` | host | 11 | Author the ISO9660 image and append the ESP partition. |
| `mkfs.vfat` | host | 11 | Format the FAT32 ESP image. |
| `mcopy` (mtools) | host | 11 | Populate the ESP image without mounting. |

The `mkirf` and `mkuki` invocations are `chroot` calls into the composed root; every other tool runs directly on the host.

## The shape of the order

The dependencies fix the order. Compose must produce the tree before anything can operate on it. The initramfs is packed before the squashfs so the rootfs image contains it. Registry seeds and feature scripts are staged before the squashfs so they ride into the rootfs image. The UKI needs the packed initramfs cpio, so it follows stage 6 (and follows the squashfs in sequence). The ISO needs the UKI. Read top to bottom, each stage consumes what the stages above it produced.

For the full field-by-field reference of every spec section named here, see [The build spec](~peiso/reference/the-build-spec). For how to actually invoke a build and what it prints, see [Running a build](~peiso/building-images/running-a-build).

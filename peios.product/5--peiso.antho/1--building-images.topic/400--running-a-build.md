---
title: Running a build
type: reference
description: "How to run peiso build: the one command and its spec argument, why it must run as root, its exit codes, the tools it needs, and the dist Makefile workflow."
related:
  - peios/peiso/reference/the-build-spec
  - peios/building-images/the-build-pipeline
  - peios/building-images/overview
  - peios/package-management/composing-a-root
---

`peiso build` takes a declarative spec and produces a bootable Peios image tree from it — it composes the package root, packs the initramfs, and layers on the optional squashfs, UKI, and ISO stages. This page covers running that command: its one argument, why it needs root, what it needs on the host, and how the `dist/prod/` workflow invokes it. For what each stage does, see [The build pipeline](~peios/building-images/the-build-pipeline); for the spec it reads, see [The build spec](~peios/peiso/reference/the-build-spec).

## Synopsis

```
peiso build [spec.toml]

peiso -h | --help | help
```

`build` is peiso's only working verb. It takes **one optional positional argument** — the path to the build spec — and defines **no flags**; anything after the spec path is ignored. The spec path is the only input to the command; everything else about the build is declared inside the spec.

When the positional is omitted, the spec path **defaults to `peiso.toml`** in the current directory:

```
$ cd dist
$ sudo peiso build          # builds ./peiso.toml
$ sudo peiso build peiso.toml   # the same, spelled out
```

`peiso -h`, `peiso --help`, and `peiso help` all print the usage text and exit. Running peiso with no arguments at all is a usage error (it prints usage and exits `2`).

## The build must run as root

The build **chroots into the composed root** to run Peios' own applets — `mkirf` to pack the initramfs, and `mkuki` to bundle the UKI — in their native environment. `chroot` is privileged, so peiso requires an effective UID of `0`.

peiso checks this **first**, before it composes anything, and fails fast with a message that tells you what to do, rather than composing for minutes and then failing at the chroot:

```
peiso: build chroots into the composed root and must run as root (try: sudo peiso build)
```

Run it under `sudo` (or as root):

```
sudo peiso build peiso.toml
```

This root requirement is the one operational difference from [`peipkg-compose`](~peios/package-management/composing-a-root), which needs no privilege because it only ever writes inside its output directory. peiso needs privilege precisely because the boot stage runs the shipped applets inside the root.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The build succeeded — the image tree (and any optional artifacts) were produced. |
| `1` | The build failed. The error is printed to stderr as `peiso: <err>` — a missing/invalid spec, not running as root, `peipkg-compose` not found, a compose failure, a missing in-root applet, or any stage that errored. |
| `2` | A usage error — no command at all, or an unknown command — with the usage text printed to stderr. |

## Prerequisites

A build uses two distinct sets of tools: programs peiso runs **on the host**, and applets it runs **inside the composed root** by way of `chroot`. Which stages use each are covered in [The build pipeline](~peios/building-images/the-build-pipeline); this section is the checklist.

### Host tools

These must be present on the build host (on `PATH`, unless noted):

| Tool | Package | Used for |
|---|---|---|
| `peipkg-compose` | peipkg | Composing the package root(s). peiso shells out to it. Located via `PATH`, a peiso-binary sibling, or `PEISO_COMPOSE` — see [Environment](#environment). |
| `mksquashfs` | squashfs-tools | Building the rootfs squashfs from the composed root (the squashfs stage). |
| `xorriso` | xorriso | Emitting the bootable `peios.iso` (the ISO stage). |
| `mkfs.vfat` | dosfstools | Building the FAT32 ESP image the ISO carries (the ISO stage). |
| `mcopy` | mtools | Copying the UKI into that ESP image (the ISO stage). |

The last three are only needed if the spec's ISO stage is enabled; `mksquashfs` only if the squashfs stage is. A minimal spec that stops at the packed root needs only `peipkg-compose`.

### In-root applets

Two applets are run **inside the composed root** via `chroot`, so they are not host tools — they must be present in the root itself, which means the **spec's manifest must install the packages that ship them**:

| Applet | Path in the root | Used for |
|---|---|---|
| `mkirf` | `/usr/bin/mkirf` | Packing the initramfs root into a cpio archive. Always run. |
| `mkuki` | `/usr/bin/mkuki` | Bundling the Unified Kernel Image (the UKI stage). |

Running the shipped applets in their own environment is deliberate: the tool that builds the initramfs is the same one the running system carries, so there is no divergence between what is tested and what runs. If `mkirf` is missing from the composed root, the build fails with a hint that the applet package (peiosutils) was not composed in.

These are package-storage paths deliberately. Peiso self-hosts before the root-level StrataFS views are mounted, so it must not depend on `/bin` or another projected view. On x86-64 the composed root must still carry the base-filesystem `/lib64 → usr/lib/x86_64-linux-peios` mapping required by the ELF ABI to start dynamically linked applets.

## Environment

peiso reads a **single** environment variable:

| Variable | Effect |
|---|---|
| `PEISO_COMPOSE` | Overrides the location of the `peipkg-compose` binary. When set, peiso uses it verbatim and skips the search below. |

When `PEISO_COMPOSE` is unset, peiso finds `peipkg-compose` by:

1. looking it up on `PATH`; then
2. falling back to a **sibling of the peiso binary itself** — the two are installed together (`go install` drops both in `GOBIN`), and `sudo`'s `secure_path` routinely drops `GOBIN` from `PATH`, hiding the sibling installed next to peiso.

If it is found by none of these, the build fails:

```
peiso: peipkg-compose not found on PATH or next to peiso (set PEISO_COMPOSE to override)
```

No other environment variables are read.

## What you supply

Running a build takes two inputs, both authored by you:

- **A `peiso.toml` spec** — the declaration of the whole image: the manifest to compose, how the initramfs is packed, and the optional squashfs, UKI, ISO, registry-seed, and feature stages. Every field is documented in [The build spec](~peios/peiso/reference/the-build-spec).
- **The peipkg-compose manifest** the spec references — the package set and repositories that compose into the root. This is an ordinary compose manifest; see [Composing a root](~peios/package-management/composing-a-root).

Everything else — the initramfs cpio, the squashfs, the UKI, the ISO — is produced by the build. peiso owns its output tree as a rebuildable artifact and clears a prior one before each run, so a rebuild always starts clean.

## The dist workflow

The reference workflow lives in the repository's `dist/prod/` directory, driven by its `Makefile`. The `root:` target is the canonical way to run a build, and it handles two operational details for you — locating peiso and elevating to root:

```make
PEISO := $(shell command -v peiso)

root: peiso.toml manifest.toml repo
	@test -n "$(PEISO)" || { echo "peiso not found on PATH — run 'go install' in ../../peiso" >&2; exit 1; }
	sudo $(PEISO) build peiso.toml
```

The target resolves `peiso` **as the invoking user**, while `PATH` is still intact, and then `sudo`-runs it by **absolute path**. That indirection matters: `sudo`'s `secure_path` drops `~/go/bin`, so a bare `sudo peiso` would not find peiso (nor the `peipkg-compose` it calls). Resolving the absolute path first sidesteps that entirely.

The whole build is then:

```
cd dist/prod
make root
```

which expands to `sudo /abs/path/to/peiso build peiso.toml` against the `dist/prod/peiso.toml` spec and its `manifest.toml` (the `repo` prerequisite publishes the medium's offline package repository first, for the spec's `[[iso.include]]`). The other `dist/prod/` targets boot the result under QEMU: `make boot` boots `peios.iso` under OVMF — the real UEFI, GPT-ESP, UKI path, the same one `dd`ing the ISO to a USB stick exercises on metal — with `boot-break` and `boot-quiet` variants, and `make boot-install` / `make boot-installed` drive the installation round trip against a scratch disk (`make clean-disk` resets it).

## What a build leaves behind

A full build (all stages enabled) produces the chain of artifacts described in [The build pipeline](~peios/building-images/the-build-pipeline). In brief:

- the composed **`root/`** tree — the package root with the packed initramfs cpio inside it;
- the **rootfs squashfs** (named by `[squashfs].out`) — written beside `root/`, not inside it;
- the **UKI** at its ESP fallback path, e.g. `boot/efi/EFI/BOOT/BOOTX64.EFI`;
- **`peios.iso`** — the bootable UEFI live medium.

The squashfs, UKI, and ISO are each optional and driven by their spec sections; a minimal build stops at the composed root plus the initramfs cpio.

## See also

- [The build spec](~peios/peiso/reference/the-build-spec) — every `peiso.toml` field the command reads.
- [The build pipeline](~peios/building-images/the-build-pipeline) — what each stage of the run does.
- [Composing a root](~peios/package-management/composing-a-root) — the manifest the spec points at.

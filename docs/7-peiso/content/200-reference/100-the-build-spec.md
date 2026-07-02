---
title: The build spec
type: reference
description: "Field-by-field reference for peiso.toml: every table and key with types, defaults and path handling, plus the exact validation rules peiso enforces."
related:
  - peiso/building-images/overview
  - peiso/building-images/the-build-pipeline
  - peios/package-management/composing-a-root
---

**`peiso.toml`** is the declarative TOML spec that drives [`peiso`](~peiso/building-images/overview). A single file describes the whole bootable image: the [peipkg-compose manifest](~peios/package-management/composing-a-root) to build the package root from, how the initramfs is packed, and the optional squashfs, UKI, ISO, registry-seed and feature stages that [the build pipeline](~peiso/building-images/the-build-pipeline) layers on top. This page documents **schema version `1`** — the only schema peiso accepts — field by field.

The spec is passed to peiso positionally and **defaults to `peiso.toml`** in the current directory:

```
sudo peiso build [spec.toml]
```

Three properties hold across the whole file:

- **TOML, parsed strictly.** An **unknown key anywhere in the spec is a hard error**, not a warning — peiso rejects the first undecoded key by name. A typo'd field fails the build rather than being silently ignored.
- **`schema` is checked first.** The spec must declare `schema = 1`; any other value (or a missing `schema`, which reads as `0`) fails with `unsupported schema`.
- **Relative paths resolve against the spec file's own directory** — never the current working directory. So a build behaves the same wherever you invoke it from. There are two flavours of path handling, and it matters which a field uses:
  - **Spec-relative paths** (`root.manifest`, `root.out`, `initramfs.manifest`, `squashfs.out`, `uki.cmdline_file`, `iso.source`, `iso.out`, `inject.src`) are made **absolute** against the spec's directory. An already-absolute value is kept as given.
  - **Root-relative paths** (`initramfs.dir`, `initramfs.cpio`, `uki.out`, `iso.efi_boot`, `inject.dest`) are **cleaned and kept relative** (any leading `/` is stripped). These double as chroot-absolute paths inside the composed root, so they are validated to **not escape** with `..` (see [Validation](#validation)).

## A complete example

A full spec that composes a root, packs the initramfs, squashes the rootfs, builds a UKI, emits a bootable ISO, and enables a feature on first boot:

```toml
schema      = 1
source_date = "2026-06-22T00:00:00Z"   # pins reproducible build timestamps

# The whole image. manifest.toml is multi-root — it composes the main system
# root into `out` and the nested initramfs root (at out/boot/initramfs) in one
# pass, so [initramfs] below needs no manifest of its own.
[root]
manifest = "manifest.toml"
out      = "root"

# How mkirf packs the already-composed initramfs root into a cpio. `dir` and
# `cpio` are root-relative: inside the chroot they are mkirf's /<dir> source and
# /<cpio> output. The peipkg database isn't needed at early boot, so it's excluded.
[initramfs]
dir     = "boot/initramfs"
cpio    = "system/boot/initramfs.cpio.gz"
exclude = ["var/lib/peipkg", "conf/peipkg"]

# Read-only rootfs image, squashed from the WHOLE composed root. `out` is written
# OUTSIDE root/ so the image can never contain itself.
[squashfs]
out         = "sysroot.squashfs"
compression = "zstd"

# Unified Kernel Image: kernel + initramfs cpio + cmdline in one EFI binary.
# cmdline_file is read from the composed root, so build-time and runtime agree.
[uki]
cmdline_file = "root/usr/share/live-boot/cmdline"
out          = "boot/efi/EFI/BOOT/BOOTX64.EFI"

# Bootable UEFI ISO built from the ESP tree at `source`, with the UKI marked as
# the EFI boot image at `efi_boot` (relative to source).
[iso]
source   = "root/boot/efi"
efi_boot = "EFI/BOOT/BOOTX64.EFI"
out      = "peios.iso"
label    = "PEIOS"

# Features this image enables on first boot (feat add <name>).
[features]
enable = ["dynamic-boot"]
```

`[squashfs]`, `[uki]`, `[iso]`, `[registry]` and `[features]` are all optional — a minimal spec is just `schema`, `[root]` and `[initramfs]`, which composes the root and packs the initramfs.

## Top-level fields

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schema` | int | **yes** | Spec schema version. Must be `1`; any other value fails. |
| `source_date` | string | no | A fixed build timestamp for reproducible artifacts, passed through to `mksquashfs`. Empty (or omitted) means epoch `0`. The format is not validated by peiso — the example uses an RFC 3339 timestamp, mirroring the compose manifest's [`source_date`](~peios/package-management/composing-a-root). |

## `[root]` — the package root (required)

The main system root, composed by shelling out to `peipkg-compose build`. Both keys are required.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `manifest` | string (spec-relative) | **yes** | The [peipkg-compose manifest](~peios/package-management/composing-a-root) to build the root from. A **multi-root** manifest composes both the main system root and the nested initramfs root in one pass. |
| `out` | string (spec-relative) | **yes** | The directory to compose into and `chroot` into. peiso owns this as a rebuildable artifact and **clears it before each build** (a single clean that also clears the nested initramfs root). |

## `[initramfs]` — packing the initramfs (required)

Describes how peiso packs the initramfs root into a cpio archive using the composed root's own [`mkirf`](~peios/boot-and-trust-establishment/mkirf) applet, run inside the chroot. `dir` and `cpio` are **required**; the rest are optional.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `dir` | string (root-relative) | **yes** | The initramfs root, relative to `root.out` (e.g. `boot/initramfs`). Inside the chroot this is mkirf's `/<dir>` source. Must not escape the root with `..`. |
| `cpio` | string (root-relative) | **yes** | The cpio output path, relative to `root.out` (e.g. `system/boot/initramfs.cpio.gz`). Inside the chroot this is mkirf's `/<cpio>` output. Must not escape the root with `..`. |
| `exclude` | array of strings | no | Globs passed to [`mkirf --exclude`](~peios/boot-and-trust-establishment/mkirf), relative to the initramfs root — paths omitted from the cpio (e.g. the peipkg database, not needed at early boot). |
| `manifest` | string (spec-relative) | no | **Legacy — normally unused.** The older *separate-compose* form: a manifest that composes the initramfs root on its own. It is normally absent because a multi-root `root.manifest` already produces the nested initramfs root, and this section then only describes how mkirf packs it. When present, peiso composes it into `root.out/<dir>` as a second, separate compose. |
| `inject` | array of tables | no | **Temporary — a packaging bypass.** Files copied straight into the initramfs root *before* mkirf runs, a stopgap for landing files (e.g. the live-boot hook) without packaging them. See below. |

### `[[initramfs.inject]]` (temporary)

Each entry copies one file into the initramfs root before it is packed. This is a **transitional mechanism** — the intended path is to ship such files in a package so a cross-root dependency pulls them into the initramfs root during compose. `src` and `dest` are both required.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `src` | string (spec-relative) | **yes** | The source file to copy. |
| `dest` | string (root-relative) | **yes** | The destination inside the initramfs root. Must not escape with `..`. |
| `mode` | string (octal) | no | Permission bits as an octal string (e.g. `"0755"`). Empty (or omitted) preserves the source file's mode. |

## `[squashfs]` — the read-only rootfs image (optional)

When present, peiso squashes the whole composed root into a read-only image (the live-boot lower layer). Presence of the table is what turns the stage on; `out` is then required.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `out` | string (spec-relative) | **yes** (when `[squashfs]` present) | The image output path. Conventionally written **outside** `root.out` so the image can never contain itself. |
| `exclude` | array of strings | no | Source-relative paths to omit from the image. |
| `compression` | string | no | The `mksquashfs -comp` value (e.g. `zstd`). Empty uses the mksquashfs default. |

## `[uki]` — the Unified Kernel Image (optional)

When present, peiso bundles a [UKI](~peios/boot-and-trust-establishment/mkuki) — kernel + initramfs cpio + kernel cmdline in one EFI binary — using the composed root's own `mkuki` applet in the chroot. You must supply the cmdline **exactly one** way: `cmdline` **or** `cmdline_file`, never both and never neither.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `cmdline` | string | conditional | The literal kernel command line. **Mutually exclusive** with `cmdline_file`. |
| `cmdline_file` | string (spec-relative) | conditional | A file holding the cmdline, read at build time. Pointing at a file inside the composed root keeps build-time and runtime single-sourced. **Mutually exclusive** with `cmdline`. |
| `out` | string (root-relative) | **yes** (when `[uki]` present) | The UKI output, relative to `root.out` — the ESP EFI path (e.g. `boot/efi/EFI/BOOT/BOOTX64.EFI`). Must not escape the root with `..`. |

## `[iso]` — the bootable ISO (optional)

When present, peiso emits a UEFI-bootable ISO9660 image (via `xorriso`) from an ESP tree. `source`, `efi_boot` and `out` are required; `label` defaults.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `source` | string (spec-relative) | **yes** (when `[iso]` present) | The ESP directory tree packed into the ISO (holding the UKI). |
| `efi_boot` | string (root-relative to `source`) | **yes** (when `[iso]` present) | The EFI boot binary (the UKI) inside the ESP tree, relative to `source` (e.g. `EFI/BOOT/BOOTX64.EFI`) — the file firmware boots from the ESP partition. peiso checks it exists before authoring the ISO. Must not escape `source` with `..`. |
| `out` | string (spec-relative) | **yes** (when `[iso]` present) | The `.iso` output path. |
| `label` | string | no | The ISO9660 volume label. Defaults to `PEIOS`. |

## `[registry]` — registry seeds auto-applied on first boot (optional)

Selects which vendor registry-seed masters (shipped by packages into `/usr/share/peios/registry.d/`) this image auto-applies on first boot. peiso stages each into the composed root's autoapply queue; peinit drains it at first boot. Selection lives here, in the image, not in the packages.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `autoapply` | array of strings | no | **Bare seed filenames** (no path separators), relative to `/usr/share/peios/registry.d/` in the composed root. Each entry is validated to be a bare filename. |

## `[features]` — features enabled on first boot (optional)

Selects which curated features (shipped by packages into `/usr/libexec/peios/features.d/`) this image enables on first boot. peiso writes a self-removing autorun script of `feat add <name>` lines; peinit runs it before Phase 2, so the services a feature creates start the same boot.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `enable` | array of strings | no | Feature names to `feat add` on first boot. Each must match feat's **name grammar** (see [Validation](#validation)); the name is embedded verbatim in a generated shell line. |

## Validation

peiso loads, decodes and validates the spec before running anything. The rules, exactly as enforced:

- **Unknown keys are rejected.** Any key the schema does not define — at any level — fails the build, naming the first offending key.
- **Schema gate.** `schema` must equal `1`, or the build fails with `unsupported schema`.
- **Required fields.** `root.manifest`, `root.out`, `initramfs.dir` and `initramfs.cpio` must all be present and non-empty. Within an optional table that *is* present, its own required keys apply: `squashfs.out`; `uki.out`; `iso.source`, `iso.efi_boot` and `iso.out`; and both `src` and `dest` on every `inject` entry.
- **No-escape path checks.** The root-relative paths `initramfs.dir`, `initramfs.cpio`, `uki.out`, `iso.efi_boot` and `inject.dest` may not be `..` or begin with `../` — they become chroot-absolute paths and must stay inside their tree. (Spec-relative paths are not subject to this check; they resolve to absolute paths.)
- **UKI cmdline mutual-exclusion.** When `[uki]` is present, **exactly one** of `cmdline` or `cmdline_file` must be set. Supplying both, or neither, is an error.
- **Registry seeds must be bare filenames.** Each `registry.autoapply` entry must be non-empty and contain no path separator (it must equal its own basename); a path component is a spec error.
- **Feature-name grammar.** Each `features.enable` entry must be non-empty, must not be `.` or `..`, and must consist only of **ASCII alphanumerics plus `-`, `_` and `.`**. This mirrors feat's own name grammar and doubles as a guard against shell metacharacters, since the name is embedded in a generated `feat add` line.
- **Inject mode.** `inject.mode`, when set, must parse as an octal integer; a malformed value fails the build.

A spec that passes all of these is what peiso hands to [the build pipeline](~peiso/building-images/the-build-pipeline).

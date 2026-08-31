---
title: The spec
type: reference
description: Every key a peiso spec may carry — the package sources, the baseline edition and version, first boot, source date, devtools and registry adjustments — with defaults and the rules each one follows.
related:
  - peios/peiso/building-images/quick-start
  - peios/peiso/building-images/the-build-pipeline
  - peios/peiso/editions-and-upgrades/release-toml
---

A spec is a TOML file. Unknown keys are errors. Relative paths resolve against the spec file's directory, not the current directory — which is also what lets several specs be [layered](#layering) into one.

```toml
[[packages.repository]]
url  = "file://../../pkgs/_pkgsOut_/"
keys = ["../../pkgs/dev-signing.pub"]

[baseline]
edition     = "Experimental"
version     = "2026.8"
first_boot  = "live"
source_date = "2026-06-22T00:00:00Z"

[devtools]
dwe = false

[registry]
add    = []
remove = []

[[package]]
name    = "bash"
version = ">= 5.2"
root    = ""

[[file]]
src  = "overlay/motd"
dest = "usr/etc/motd"
sddl = "O:SYG:SYD:(A;;GA;;;SY)(A;;FR;;;WD)"

[[autorun]]
src  = "scripts/setup.sh"
name = "50-setup"

[[feature]]
name  = "dynamic-boot"
state = "enable"

[[medium]]
src  = "docs/"
dest = "docs"

[squashfs]
compression = "zstd"
exclude     = []

[initramfs]
exclude = ["var/state/peipkg", "lcl/conf/peipkg"]

[boot]
cmdline_extra = ""
```

## Layering

A build may name several specs, and they are layered left to right:

```sh
peiso root shared.toml profiles/kernel-only/peiso.toml
```

Each file is read and resolved on its own first, **against its own directory**. A `file://` repository URL, a `[[file]]` `src`, an `[[autorun]]` script: each means what it says where it is written, so a layer stays movable and two layers in different directories can each name paths beside themselves.

Only the layering as a whole has to be a complete spec. The two requirements no single file can be held to — an edition, and at least one repository — are checked after the merge, and the error names every layer rather than guessing which should have carried the key. So this is a spec:

```toml
# shared.toml — where packages come from. A property of the checkout.
[[packages.repository]]
url  = "file://../pkgs/_pkgsOut_/"
keys = ["../pkgs/dev-signing.pub"]
```

```toml
# profiles/kernel-only/peiso.toml — what is being built. A property of
# this one build.
[baseline]
edition    = "kernel-only"
first_boot = "none"
```

…while neither file is one alone. That split is the point: many builds can share one statement of where packages come from without repeating it, and without a build's own file having to restate anything it does not care about.

### What a layer does to the one below

| | |
|---|---|
| Scalars | A layer that states one overrides; a layer silent about one leaves it alone. `edition`, `version`, `first_boot`, `source_date`, `squashfs.compression`, `squashfs.level`, `boot.cmdline_extra`, `devtools.dwe`. |
| Lists | Accumulate in layering order: `[[packages.repository]]`, `[[package]]`, `[[file]]`, `[[autorun]]`, `[[feature]]`, `[[medium]]`, `registry.add`, `registry.remove`, `squashfs.exclude`. Repositories are searched in that order, so a base layer's sources come before a later layer's additions. |
| `initramfs.exclude` | Replaces rather than accumulates. Absent and empty already mean different things there — the default list, and nothing — and appending would leave a layer no way to write either. |

A single spec is just a layering of one, so nothing above changes what one file on its own means.

## `[[packages.repository]]`

Where packages come from. At least one is required; several are searched together, in order.

| Key | | |
|---|---|---|
| `url` | required | A `file://` path or an `http(s)://` URL. A relative `file://` path is resolved against the spec's directory. A `file://` directory holding a repository descriptor (`repo.json`) is used as a repository; one holding only `.peipkg` files is used as a directory of packages. |
| `keys` | optional | Public key files (raw 32 bytes or PEM) of the signers of this source's packages. The medium repository must list a package's signer to carry it, and a plain directory of packages publishes no keys of its own — so a pool source needs this. |
| `trust_anchors` | optional | Key fingerprints to verify a repository source against. Ignored for a directory of packages. |

## `[baseline]`

| Key | | |
|---|---|---|
| `edition` | required | The edition name as written on the box: `"Experimental"`. The package is `peios-` plus the name lowercased with each run of whitespace replaced by a hyphen: `"Pro Desktop"` → `peios-pro-desktop`. |
| `version` | optional | The edition version to build, e.g. `"2026.8"`. Absent means the newest available. Written without the packaging revision; `2026.8` matches `2026.8-1` and any later revision. |
| `first_boot` | optional, default `"live"` | What the medium boots into. `"live"` adds `live-boot` to the root. `"none"` says the composition is not a medium at all and adds no boot flavour — for a root something else will boot, or make bootable its own way; `peiso iso` refuses it. `"install"` is reserved and currently refused. |
| `source_date` | optional | An RFC 3339 timestamp stamped on everything the build produces — compose's source date, the repository indexes, every squashfs entry, the ISO. Absent means the build time, which is not reproducible. |

## `[devtools]`

| Key | | |
|---|---|---|
| `dwe` | optional, default `false` | Add the Developer Workstation Environment: `peios-dwe` in the root and the `dwed-service` seed. The build directory and ISO gain a `-dwe` suffix. A DWE image is ownable by whoever can reach its vsock; it is for development. |

## `[registry]`

Adjust the seeds the edition auto-applies. Names are seed names — `login-console`, not `login-console.reg` — resolved to `/usr/share/regim/<name>.reg` in the composed root.

| Key | | |
|---|---|---|
| `add` | optional | Seeds to stage in addition to the release's. Each must be shipped by a package in the root; a name nothing ships is an error. |
| `remove` | optional | Seeds from the release's list (or from `add`, or the DWE seed) not to stage. |

The starting list comes from the edition's [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml), not from the spec. A spec never has to name a seed the release already applies.

## `[[package]]`

A package to carry beyond the edition. Repeat the table for each.

| Key | | |
|---|---|---|
| `name` | required | The package name, resolved from the spec's sources with its dependencies. |
| `version` | optional | A constraint in peipkg's grammar — `"5.2"`, `">= 5.2"`, `">= 5.2, < 6"`. Absent means any version, newest wins. |
| `root` | optional | `"initramfs"` to place the package in the initramfs root — an extra boot hook, say. Absent means the main root. |

An addition rides on the same resolution as the edition, so a package that conflicts with the edition's closure fails the build rather than quietly displacing something. There is no way to remove a package: the edition's closure is what makes the image a Peios, and everything else is here only because a `[[package]]` put it there.

## `[[file]]`

A file injected into the root, outside any package. [Customising an image](~peios/peiso/building-images/customising-an-image) discusses the cost.

| Key | | |
|---|---|---|
| `src` | required | Host path, relative to the spec; must exist and be a file. |
| `dest` | required | Path inside the root: relative (a leading `/` is dropped), cleaned, and not escaping the root. |
| `sddl` | optional | The file's security descriptor in SDDL, written into the image as `security.peios.sd`. Refused for a `dest` under `boot/initramfs/`. |

## `[[autorun]]`

A script placed executable in `/lcl/policy/autorun.d/`.

| Key | | |
|---|---|---|
| `src` | required | Host path, relative to the spec. |
| `name` | optional, default the file's name | The entry's name in the directory; ordering is by name. peiso's own entries are `10-apply-seeds.sh` and `20-features.sh`. |

## `[[feature]]`

| Key | | |
|---|---|---|
| `name` | required | A feature under `/libexec/features/`, present in the root. |
| `state` | optional, default `"enable"` | `"enable"` runs `feat add` (install then enable); `"install"` runs `feat install` only. |

## `[[medium]]`

A file or directory placed in the ISO's data area, reachable at `/media/peios/<dest>` on the live system.

| Key | | |
|---|---|---|
| `src` | required | Host path, relative to the spec; a file or a directory. Symlinks are refused — an ISO9660 data area cannot carry them. |
| `dest` | required | Path on the medium, relative and cleaned. |

## `[squashfs]`

| Key | | |
|---|---|---|
| `compression` | optional, default `"zstd"` | Passed to `mksquashfs -comp`. |
| `level` | optional, default the compressor's own | Passed to `mksquashfs -Xcompression-level`; must be a level the chosen compressor accepts. A low level trades image size for build time — the knob a [dev layer](~peios/peiso/building-images/running-a-build) sets, never a release. |
| `exclude` | optional | Root-relative paths left out of the image (a directory takes its subtree). |

## `[initramfs]`

| Key | | |
|---|---|---|
| `exclude` | optional, default `["var/state/peipkg", "lcl/conf/peipkg"]` | Globs, relative to the initramfs root, that `mkirf` leaves out. Setting it replaces the default; `[]` excludes nothing. |

## `[boot]`

| Key | | |
|---|---|---|
| `cmdline_extra` | optional | Appended to the kernel command line the boot package ships, and baked into the UKI. There is no full replacement. |

## What the spec cannot say

No package list, no output paths, no ISO label, no full command-line replacement. Everything the spec adds — packages, files, scripts, features, medium contents — is an addition to a release, recorded in `customisations.toml`; nothing in it can redefine what the release is, and nothing in it can quietly produce a different image from the same file. What a Peios contains is the edition package's to say; peiso builds what it says, plus what you asked for on top.

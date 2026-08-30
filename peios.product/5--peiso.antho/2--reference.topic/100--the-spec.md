---
title: The spec
type: reference
description: Every key a peiso spec may carry — the package sources, the baseline edition and version, first boot, source date, devtools and registry adjustments — with defaults and the rules each one follows.
related:
  - peios/peiso/building-images/quick-start
  - peios/peiso/building-images/the-build-pipeline
  - peios/peiso/editions-and-upgrades/release-toml
---

A spec is a TOML file. Unknown keys are errors. Relative paths resolve against the spec file's directory, not the current directory.

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
```

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
| `first_boot` | optional, default `"live"` | What the medium boots into. `"live"` adds `live-boot` to the root. `"install"` is reserved and currently refused. |
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

## What the spec cannot say

The spec has no package list, no initramfs or squashfs or UKI section, and no way to inject files. Those were the previous builder's spec, and each was a way for an image to drift from the release it claimed to be. What a Peios contains is the edition package's to say; peiso builds what it says.

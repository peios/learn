---
title: Composing a root
type: reference
description: "peipkg-compose builds a fresh, fully package-owned root directory from a declarative manifest, offline and deterministically. This page covers the two commands lock and build, the manifest and its field tables, the generated lock file, how named roots and claims settle in a composed image, what ends up in the tree, and what compose deliberately does not do."
related:
  - peios/package-management/overview
  - peios/package-management/named-roots
  - peios/package-management/claims
  - peios/package-management/repositories-and-trust
---

`peipkg` mutates a running system in place: every change is an atomic, reversible [transaction](~peios/package-management/transactions-and-recovery) against a live root. **`peipkg-compose`** is its counterpart on the assembly side. Instead of changing a system that already exists, it builds a fresh, fully package-owned root directory from nothing — offline, deterministically, and verifiably, with no live system involved anywhere in the process.

`peipkg-compose` is a separate binary, not a `peipkg` subcommand. You run `peipkg-compose`, and its two verbs (`lock` and `build`) are the whole of its command surface.

Given a declarative TOML **manifest** that names a package set and the repositories to draw it from, compose produces a populated root directory: package payloads laid out at their installed paths, a seeded peipkg state database at `var/lib/peipkg/db.sqlite`, and each repository written out as `conf/peipkg/<name>.repo`. The result is a legitimate peipkg-managed system — once booted it can manage itself, and repository trust bootstraps on its first `refresh`.

It is meant for **image builders** — an outer image-assembly tool, or a person standing one up by hand. Because it only ever writes inside the output directory and never touches the host `/`, it is safe to run on a non-Peios host, and even on a host of a different architecture from the image being built.

## The mental model

Compose runs in two stages, and the two verbs map onto them.

**Stage 1 — resolve.** Read the manifest, resolve the requested package set against the declared repositories into a complete transitive closure, verify each repository's trust chain, and pin the result. This stage needs repository metadata; its output is the **lock file**.

**Stage 2 — assemble.** Fetch the pinned `.peipkg` payloads, verify them against the lock's hashes, and lay out the root directory. This stage needs only package bytes, not metadata, and can run fully air-gapped once a lock exists.

`lock` does Stage 1 alone. `build` does Stage 2, running Stage 1 first when it needs to. Everything build-stamped in the output is derived from the manifest's `source_date`, so given the same manifest, lock, and packages, the output is **reproducible**.

## `peipkg-compose lock`

```
peipkg-compose lock <manifest> [-o <lock>]
```

Resolve the manifest against its repositories, verify the trust chain, and write the lock file. `lock` builds nothing — it produces only the lock.

The `<manifest>` positional is required. Flag order is not significant: the manifest may appear before or after `-o`.

| Option | Effect |
|---|---|
| `-o <lock>` | Output lock path. Defaults to the manifest path with a trailing `.toml` replaced by `.lock.toml` — so `image.toml` locks to `image.lock.toml`. Only the single-dash `-o` form exists here; there is no `--out` for `lock`. |

## `peipkg-compose build`

```
peipkg-compose build <manifest> --out <dir> [--locked | --update]
```

Assemble the root directory. The `<manifest>` positional is required; flag order is not significant.

`--out <dir>` is required — omitting it is a usage error. The directory named by `--out` must not already exist: compose creates it, and refuses to build into or over an existing tree.

| Option | Effect |
|---|---|
| `--out <dir>` | The output root directory. Required. Must not already exist. |
| `--locked` | Require an existing lock and do **not** resolve. Fails if no lock is present. Fetches only package bytes, taking integrity from the lock's hashes — the air-gap-friendly path. |
| `--update` | Re-resolve from scratch, overwrite the lock, then build. |

`--locked` and `--update` are **mutually exclusive**.

With neither flag, `build` follows Cargo's `build` / `Cargo.lock` behaviour:

- if the sibling lock is **missing**, it resolves, writes the lock, and builds;
- if the sibling lock is **present**, it verifies the lock still matches the manifest and then builds.

Use `--locked` for reproducible or air-gapped rebuilds where no metadata resolution should happen at all, and `--update` when you want to pick up newly-available versions and refresh the lock in the same run.

## The manifest

The manifest is a TOML file describing the package set to assemble and the repositories to draw it from. Any filename works — it is passed positionally — and its sibling lock is `<stem>.lock.toml`. The manifest and the lock are **tool-local build artifacts**; they are not an on-wire Peios format.

The parser is strict: an unknown key anywhere in the manifest is a hard error, not a warning. A mistyped field name fails the build rather than being silently ignored.

```toml
schema = 1
arch = "x86_64"
source_date = "2026-07-01T00:00:00Z"

local_packages = ["./bootstrap/*.peipkg"]

[[repository]]
name = "core"
base_url = "https://repo.example.org/core"
priority = 10
signature_policy = "required"
trust_anchors = ["a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]

[[root]]
name = "initramfs"
path = "boot/initramfs"

[[package]]
name = "base-system"

[[package]]
name = "nginx"
version = ">=1.27, <1.28"
repository = "core"

[[package]]
name = "live-boot"
root = "initramfs"
```

### Top-level fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema` | int | yes | Manifest schema version. Must be `1`. |
| `arch` | string | yes | Target architecture; becomes the image's primary architecture. |
| `source_date` | string | yes | An RFC 3339 timestamp. Fixes every build-stamped time in the output, for reproducibility — the manifest's `SOURCE_DATE_EPOCH`. |
| `local_packages` | array of strings | no | Paths or globs of local `.peipkg` files. A bootstrap path for packages that live in no repository. |
| `[[repository]]` | array of tables | no | Package sources. Also written into the image as `.repo` files. |
| `[[root]]` | array of tables | no | Named roots, for a multi-root image. |
| `[[package]]` | array of tables | yes | The packages to install. Must be present and non-empty — an empty package set is an error. |

### `[[repository]]`

A repository table has the same shape as a [`.repo` file](~peios/package-management/repositories-and-trust). These entries drive metadata fetch and trust verification during the build, **and** are written verbatim to `conf/peipkg/<name>.repo`, so the booted system inherits the same repositories and the same trust anchors.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | Repository name; also the `.repo` filename stem. |
| `base_url` | string | yes | Where the repository's index and packages are served from. |
| `priority` | int | no | Selection priority. Default `50`. |
| `signature_policy` | string | no | `required` (default) or `optional`. |
| `trust_anchors` | array of strings | no | Hex key fingerprints trusted to sign this repository's index. |
| `allow_insecure_transport` | bool | no | Permit non-TLS transport. Default `false`. |
| `min_index_version` | int | no | Reject an index older than this version. |

### `[[package]]`

Each package table names one package to install. Package **identity is `(root, name)`** — the same package may be requested in more than one root, but a duplicate `(root, name)` pair is an error.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | The package to install. |
| `version` | string | no | A version **constraint** — a range like `">=1.27, <1.28"` or an exact pin like `"9.9.1"`. Omitted, or `"*"`, means any version and the resolver picks the newest. |
| `repository` | string | no | Pin the source repository. Must name a declared `[[repository]]`. |
| `root` | string | no | Target a declared `[[root]]` — like [`peipkg install --root`](~peios/package-management/named-roots). Empty means the package's own `default_root` if it has one, otherwise the anchor root. |

There is no `default_root` key in the manifest. `default_root` is a property each package carries from its repository index, and compose honours it automatically whenever a package's `root` is unset — just as the live consumer does.

### `[[root]]`

Each root table registers a [named root](~peios/package-management/named-roots) in the built image.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | A single named-root segment matching `[a-z0-9][a-z0-9_-]*` — no dots. |
| `path` | string | yes | Location relative to the output root. May not be absolute, may not escape with `..`, and may not be `.`. |

## The lock file

The lock is generated by `lock`, or written implicitly by a default or `--update` build. Its header reads *generated by peipkg-compose — do not hand-edit*; it is never edited by hand.

For the full transitive package closure, the lock pins each package's exact **version**, **architecture**, **source repository** (or `local` for a local `.peipkg`), the **fetch URL**, and the content **SHA-256 hash** of the `.peipkg`. It records each package's target root when that is not the anchor, along with the manifest's `arch` and `source_date` and a **digest of the manifest**.

A build refuses a lock that no longer matches its manifest. A mismatched `arch`, a mismatched `source_date`, or a changed manifest digest all reject the lock. On the default path the error tells you to re-run with `--update` to refresh it.

The two explicit flags pin down the two ends of this behaviour:

- **`build --locked`** requires the lock to already exist and does no resolution at all — the reproducible, air-gapped rebuild.
- **`build --update`** re-resolves from scratch and rewrites the lock.

An unattended compose run cannot authorise the elevated actions that the live consumer would stop and prompt for. Rather than fail the build, compose surfaces those as stderr warnings. See [Elevated authorisation](~peios/package-management/dependency-resolution) for what those actions are.

## Named roots and claims in a composed image

A composed image can be multi-root, and both mechanisms settle more simply here than on a live system — the detail lives on their own pages; this is only how compose relates to them.

**Named roots.** Each `[[root]]` becomes a [named-root](~peios/package-management/named-roots) registry entry in the built image's database, so the booted system resolves `--root <name>` and cascades upgrades into those roots. Every root is a subdirectory nested under the single `--out` tree, and the whole multi-root image is assembled as **one tree** — compose needs none of the consumer's cross-root transaction machinery. The repositories and the named-root registry live at the anchor root.

**Claims.** A fresh build is the simplest case of [claim](~peios/package-management/claims) reconciliation: there are no incumbents and exactly one known, closed package set, so every provided claim is auto-claimed. When two packages provide the same claim, the holder is chosen deterministically — the lexicographically smallest package name, matching `peipkg install`. Claim symlinks are written with targets relative to the link's own directory, so the root stays self-contained and relocatable.

## What ends up in the root

A successful build leaves a directory that is a valid peipkg-managed system:

- every package's payload laid out at its **installed paths**;
- a seeded peipkg state database at `var/lib/peipkg/db.sqlite`, recording the installed set, the named-root registry, and the settled claims;
- each declared repository written to `conf/peipkg/<name>.repo`, so the booted system inherits its repositories and their trust anchors.

The build is atomic as a whole tree. Because `--out` must not already exist, compose assembles into a sibling staging directory on the same filesystem and, on success, renames it into place atomically. A failed or interrupted run leaves the staging directory behind for inspection rather than a half-populated `--out` — there is no partial output to clean up or mistake for a finished one.

## What compose does not do

Compose's contract stops at producing a valid peipkg root. It is deliberately narrow.

- **Not a full image builder.** It produces only a directory tree — no bootloader, kernel, initramfs contents, registry seed, or peinit wiring. Those belong to whatever assembles the image around it.
- **Not a live-system tool.** It never touches the host `/`. There is no three-phase transaction, no commit boundary, no rollback journal, and no crash-recovery — the output is disposable, and its only atomicity is the single whole-tree rename above.
- **Not the producer side.** It does not build or sign `.peipkg` files and it does not serve repositories — those are the separate `peipkg-build`, `peipkg-repo`, and `peipkg-manager` tools. Compose consumes ordinary PSD-009 packages and repositories unchanged.
- **No side effects.** `ldconfig`, `depmod`, and `man-db` are not run; no KACS security descriptors are applied; no audit events are emitted. A booted system runs those itself.

No environment variables are read, and there is no `--version` flag.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success — or the help output (`-h`, `--help`, `help`). |
| `1` | A compose operation failed — resolution, trust verification, a fetch, a hash mismatch, a stale lock a `--locked` build could not use, or a file operation. |
| `2` | A usage error — no arguments, an unknown verb, a missing manifest, a missing `--out`, extra arguments, `--locked` with `--update`, or a bad flag. |

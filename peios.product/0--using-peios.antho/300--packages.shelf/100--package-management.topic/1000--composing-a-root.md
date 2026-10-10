---
title: Composing a root
type: how-to
description: Build a fresh package-managed tree, choose whether to reuse or update its lock, check the result, and find the complete image-builder interface.
related:
  - peios/package-management/overview
  - peios/package-management/named-roots
  - peios/package-management/claims
  - peios/package-management/repositories-and-trust
---

Use the separate **`peipkg-compose`** binary when you need a new package-owned
root directory for an image. Use `peipkg` to maintain a root that already
exists. Compose does not produce a bootable image by itself or run feature
setup scripts.

## Build and check a new tree

1. Prepare a manifest with the intended architecture, timestamp, repositories,
   package set and any named roots. Verify the repository anchors through a
   trusted channel. The [manifest reference](~peios/peipkg/installation-roots/compose-commands-and-manifest#the-manifest) gives every
   field and a complete example.
2. Choose an output directory that does **not** exist. Compose refuses an
   existing tree; do not point it at a live installation.
3. Resolve and record the package set, then build from that lock:

   ```
   peipkg-compose lock image.toml
   peipkg-compose build image.toml --out ./root --locked
   ```

4. Read the build outcome and warnings. If the build fails or is interrupted,
   the staging directory is left for inspection; it is not the finished root.
5. Inspect the successful output's package records and files, for example with
   `peipkg --root ./root list` and `peipkg --root ./root verify` where peipkg is
   available. Check security metadata required by the image separately.

A fresh tree includes package files, a package database and repository
configuration. It does not include recorded repository trust from the build.
On the booted system, check that configuration and deliberately run
`peipkg repo add <name>` for each source you choose to trust. Configuration is
[not a completed trust ceremony](~peios/package-management/repositories-and-trust#adding-a-repository-your-system-already-carries).

## The mental model

`lock` resolves the package set; `build` assembles it. Keeping the same manifest,
lock and package bytes makes the selected inputs repeatable. For the resolution,
verification and assembly internals, see the
[composition reference](~peios/peipkg/installation-roots/composing-a-root).

## `peipkg-compose lock`

```
peipkg-compose lock <manifest> [-o <lock>]
```

Creates a lock without building a tree. `image.toml` defaults to
`image.lock.toml`. Only `-o` selects another lock path; there is no `--out`
for this verb. See the [full lock interface](~peios/peipkg/installation-roots/compose-commands-and-manifest#peipkg-compose-lock).

## `peipkg-compose build`

```
peipkg-compose build <manifest> --out <dir> [--locked | --update]
                     [--dangerously-bypass-path-restrictions]
                     [--record-xattrs <file>] [--no-dependencies]
```

- Use `--locked` to require an existing matching lock and do no metadata
  resolution. Package bytes must still be available.
- Use `--update` to resolve again and overwrite the lock before building.
- With neither flag, a missing lock is created; an existing lock must match
  the manifest. `--locked` and `--update` cannot be combined.
- `--out` is required, and its directory must not already exist.

The [complete build options](~peios/peipkg/installation-roots/compose-commands-and-manifest#peipkg-compose-build) explain the explicit
path-restriction grant, recording security attributes, and `--no-dependencies`.
That last option deliberately creates a tree that is not self-sufficient;
it leaves signature and hash verification enabled and requires a lock made
in the same mode. Do not add it merely to get past a missing dependency.

## The manifest

The manifest is strict TOML: unknown keys, an empty package set, undeclared
repository or root references, and duplicate `(root, name)` requests are errors.
The complete schema and sample are in the [manifest reference](~peios/peipkg/installation-roots/compose-commands-and-manifest#the-manifest).

### Top-level fields

See [top-level fields](~peios/peipkg/installation-roots/compose-commands-and-manifest#top-level-fields) for `schema`, `arch`, `source_date`,
local packages, repositories, roots and package requests.

### `[[repository]]`

See [repository fields](~peios/peipkg/installation-roots/compose-commands-and-manifest#repository) for sources, priorities and trust policy.
These settings are also written into the composed system as `.repo` files.

### `[[package]]`

See [package fields](~peios/peipkg/installation-roots/compose-commands-and-manifest#package) for names, version constraints, source pins
and target roots. There is no manifest-level `default_root` key; packages can
carry their own default placement.

### `[[root]]`

See [root fields](~peios/peipkg/installation-roots/compose-commands-and-manifest#root) for names and relative paths. A root path cannot
be absolute, escape through `..`, or be `.`.

## The lock file

The generated lock pins the package set. Do not hand-edit it or use `--update`
just to suppress a mismatch without reviewing the changed inputs. See the
[lock contract](~peios/peipkg/installation-roots/compose-commands-and-manifest#the-lock-file) for digest, architecture and timestamp checks.
Elevated actions that would prompt in a live install are emitted as warnings
during unattended composition, so read them before using the image.

## Named roots and claims in a composed image

All roots are built under one output tree. The composer records named roots
and selects claim holders for the fresh package set; no installed incumbents
exist to preserve. See [the detailed rules](~peios/peipkg/installation-roots/compose-commands-and-manifest#named-roots-and-claims-in-a-composed-image)
for deterministic holder selection and relocatable links.

## What ends up in the root

The output contains payloads, `var/lib/peipkg/db.sqlite` and repository files
under `lcl/conf/peipkg/`. A successful build renames the whole staged tree into
place. See [the output contract](~peios/peipkg/installation-roots/compose-commands-and-manifest#what-ends-up-in-the-root) before treating
an interrupted build's staging directory as a usable artifact.

## What compose does not do

The outer image builder is responsible for boot integration, runtime caches
and feature setup. Compose runs no post-install maintenance steps and emits
no audit events. It does not build or sign the packages it consumes.

The references disagree on security-descriptor materialisation; the CLI
interface documents `--record-xattrs`, while an implementation summary says
no descriptors are materialised. Inspect the attributes or recorded output
needed by your image. The [full limitations and interface differences](~peios/peipkg/installation-roots/compose-commands-and-manifest#documentation-differences-to-check)
retain those details rather than assuming either behaviour is universal.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success, or help output (`-h`, `--help`, `help`) |
| `1` | Resolution, verification, fetch, lock or filesystem failure |
| `2` | Usage error, including a missing manifest or `--out`, or conflicting flags |

For exact cases and the absence of environment-variable and `--version`
interfaces, see the [complete command reference](~peios/peipkg/installation-roots/compose-commands-and-manifest#exit-status).

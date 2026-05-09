---
title: Anatomy of a Recipe
type: concept
description: A recipe describes one source package — how to build it, how to split its outputs, and how the build farm should detect new upstream versions. Two files, four TOML sections.
related:
  - peios-packages/authoring-recipes/build-scripts
  - peios-packages/authoring-recipes/multi-package
  - peios-packages/authoring-recipes/tracking-upstream
  - peios-packages/reference/recipe-format
---

A **recipe** is a directory containing two files. They describe everything needed to turn an upstream source tree into one or more `.peipkg` files for distribution.

```
recipes/libfoo/
├── peipkg.toml      # the structured description
└── build.sh         # the build script
```

Anything in the recipe directory other than these two files is ignored. The directory's name is the recipe's identifier, used in logs, webhooks, and the build farm's `/status` output.

## The two files

`peipkg.toml` carries facts: name, license, dependencies, file lists, upstream tracking. It is read by multiple tools — `peipkg-build` for the build sections, `peipkg-manager` for the upstream sections.

`build.sh` is the executable script that produces the staged file tree. Its signature is fixed: `peipkg-build` invokes it with environment variables for source and destination, and the script's job is to populate `$DESTDIR/`.

## The four sections of `peipkg.toml`

The recipe file has four top-level sections, partitioned across the two tools that read it:

| Section | Owner | Purpose |
|---|---|---|
| `[meta]` | `peipkg-build` | Shared facts: license, homepage, the build script path. |
| `[[package]]` | `peipkg-build` | One stanza per output `.peipkg`. Carries name, architecture, file globs, dependencies, side effects. |
| `[upstream]` | `peipkg-manager` | Where source lives, how to recognise version tags. |
| `[watch]` | `peipkg-manager` | How the build farm learns about new versions (webhook, poll interval). |

`peipkg-build` ignores `[upstream]` and `[watch]` entirely; `peipkg-manager` reads them to know what to build. Each tool tolerates sections it doesn't own, so the recipe file is one document with one git history regardless of which tool's behaviour you're tweaking.

> [!NOTE]
> The strictness rule applies *within* a section: an unknown key under `[meta]` or `[[package]]` is rejected as a typo, but unknown top-level sections pass through silently. So if a recipe has `[meta].homepag` (typo of `homepage`), `peipkg-build` errors out. If it has `[upstream]`, `peipkg-build` ignores it.

## A complete example

```toml
[meta]
license = "Zlib"
homepage = "https://zlib.net"
build_script = "build.sh"

[[package]]
name = "libz"
architecture = "x86_64"
description = "zlib compression library — runtime"
dependencies = [{ name = "libc" }]
side_effects = ["ldconfig"]
files = [
  "usr/lib/x86_64-linux-peios/libz.so.1",
  "usr/lib/x86_64-linux-peios/libz.so.1.*",
]

[[package]]
name = "libz-dev"
architecture = "x86_64"
description = "zlib development files"
dependencies = [
  { name = "libz", same_build = true },
  { name = "libc-dev" },
]
files = [
  "usr/include/**",
  "usr/lib/x86_64-linux-peios/libz.so",
  "usr/lib/x86_64-linux-peios/libz.a",
  "usr/lib/x86_64-linux-peios/pkgconfig/**",
]

[upstream]
git = "https://github.com/madler/zlib"
tag_pattern = "^v(\\d+\\.\\d+\\.\\d+)$"
peios_revision = 1

[watch]
github_webhook = true
poll_interval = "1h"
```

This recipe produces *two* `.peipkg` files per build: `libz_<version>_x86_64.peipkg` (runtime) and `libz-dev_<version>_x86_64.peipkg` (development). Both come from one invocation of `build.sh`.

## What's not in the recipe

A recipe is intentionally *version-agnostic*. The version isn't in `peipkg.toml`; the build farm derives it from each upstream tag the `[upstream]` section matches.

That is why the recipes repository is **stable**: routine version updates don't touch the recipe at all. New upstream tag → farm picks it up → same recipe builds it. Recipes only change when the build script needs fixing, when a new package is added, or when the file layout shifts.

If you're publishing a single package by hand (no farm), `peipkg-build` takes the version on the command line via `--version`. That's the same shape the farm uses internally; the recipe stays the same.

## Where each section is documented

- [Build scripts](./build-scripts) — what `build.sh` receives and what it must produce.
- [Multi-package recipes](./multi-package) — when to split into runtime/`-dev`/`-doc`, how `[[package]].files` globs work, and the `same_build` shorthand.
- [Dependencies](./dependencies) — how to declare what your package needs.
- [Tracking upstream](./tracking-upstream) — `[upstream]` and `[watch]` in detail, including the regex patterns and webhook setup.
- [Recipe format reference](../reference/recipe-format) — flat schema reference; useful when writing or reviewing recipes mechanically.

The normative spec for the recipe format lives in [PSD-009 appendix A.2](../../../specs/psd-009--peipkg/v0.22/8-appendix-a/2-recipe-format).

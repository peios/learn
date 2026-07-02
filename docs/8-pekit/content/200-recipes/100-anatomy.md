---
title: Anatomy of a recipe
type: concept
description: "A walk-through of the files that make up a pekit recipe: pekit.toml and its top-level sections, the supporting package/env/keyring/workspace files, how pekit locates a recipe, and the PEKIT_* environment contract every target command runs against."
related:
  - pekit/using-pekit/overview
  - pekit/using-pekit/commands-and-targets
  - pekit/recipes/sources
  - pekit/recipes/versions
  - pekit/recipes/packages
  - pekit/reference/recipe-format
---

A **recipe** is not a single file — it is a directory. One file, `pekit.toml`, is the recipe proper; the others beside it describe what to package, which environment to build in, and which secrets to sign with. This page walks through that file set, then focuses on `pekit.toml` itself and the one interface every recipe author leans on: the `PEKIT_*` environment variables that pekit hands to each target command.

## The recipe directory

Everything pekit needs to build one piece of software lives in a single directory. A rich recipe looks like this:

```text
mypkg/
├── pekit.toml                 # the recipe: source, targets, env, wrap, delegate
├── package.pekit.toml         # base package: files, symlinks, dependencies, metadata
├── packages.pekit/            # (optional) extra package members, one file each
│   ├── docs.package.pekit.toml
│   └── dev.package.pekit.toml
├── env.pekit.toml             # (optional) reusable environment / wrapper
├── prod.keyring.pekit.toml    # (optional) named keyring for signing and secrets
└── ...
workspace.pekit.toml           # (optional) one level up — groups recipes into a workspace
```

Only `pekit.toml` is required. The rest are opt-in and each has its own page:

| File | Purpose | Page |
|---|---|---|
| `pekit.toml` | The recipe: where source comes from, how to build/test/install/clean it, shared env. | this page |
| `package.pekit.toml` | The base package: how staged output maps into a `.peipkg`, plus dependencies and metadata. | [Package files](~pekit/recipes/packages) |
| `*.package.pekit.toml`, `packages.pekit/` | Additional package **members** for a recipe that produces more than one package. | [Multi-package recipes](~pekit/recipes/multi-package) |
| `env.pekit.toml`, `*.env.pekit.toml` | Reusable environment variables and a shell **wrapper** to run commands under. | [Environments and keyrings](~pekit/recipes/environments-and-keyrings) |
| `*.keyring.pekit.toml` | Named collections of secrets exported into the build as `PEKIT_KEYRING_*`. | [Environments and keyrings](~pekit/recipes/environments-and-keyrings) |
| `workspace.pekit.toml` | Sits **one level up** and groups a directory of recipes into a workspace pekit can drive as a unit. | [Workspaces](~pekit/workspaces/workspaces) |

pekit discovers the package, env, and keyring files by their fixed names in the recipe directory (`packages.pekit/` is searched as an alternative location for package files). The base package file may live at `package.pekit.toml` **or** `packages.pekit/package.pekit.toml`, but not both. The supporting-files reference lists every name and location: [Supporting files](~pekit/reference/supporting-files).

## `pekit.toml`

The recipe file is a TOML document with a small, fixed set of top-level keys. pekit is strict: any key it does not recognise is an error, caught when the recipe loads. The recognised keys are exactly:

`out_dir`, `env`, `wrap`, `source`, `delegate`, and the four target sections `build`, `test`, `install`, `clean`.

The one pekit itself ships with is deliberately minimal:

```toml
out_dir = "out"

[build]
command = "go build -trimpath -o \"$PEKIT_OUT/pekit\" ./cmd/pekit"

[test]
command = "go test ./..."

[install]
command = "go install ./cmd/pekit"

[clean]
command = "go clean ./..."
```

A fuller recipe that fetches an external source and uses more of the surface:

```toml
# Where pekit stages its output. Managed by pekit; removable by `clean`.
out_dir = "out"

# Environment variables layered onto every target command.
[env]
CARGO_TERM_COLOR = "never"

# Wrapper: every target command runs inside this. {{command}} is substituted
# with the actual build script exactly once.
[wrap]
command = "nix develop --command sh -c {{command}}"

# Where the source tree comes from, and which versions exist.
[source.git]
url = "https://github.com/BurntSushi/ripgrep.git"
ref = "{{version}}"
versions = ">=13.0.0, <=14.1.1"
tag_regex = '^(\d+\.\d+\.\d+)$'

# Borrow selected behaviour from a pekit.toml inside the fetched source.
[delegate]
env = true

# Named build targets. `needs` names other build targets to stage first.
[build.main]
command = "cargo build --release && cp target/release/rg \"$PEKIT_OUT/rg\""

[build.completions]
command = "cp complete/_rg \"$PEKIT_OUT/_rg\""
needs = ["main"]

[test]
command = "cargo test --release"
needs = ["main"]

[install]
command = "cargo install --path . --root \"$PEKIT_OUT\""

[clean]
command = "cargo clean"
```

The top-level keys break down as follows:

- **`out_dir`** — the directory pekit stages everything under, relative to the recipe unless absolute. Defaults to `"out"`. This is pekit's **managed** output: `pekit clean` may remove it wholesale, so keep nothing precious there. It holds fetched sources, per-target staging directories, and written `.peipkg` files.
- **`[env]`** — a table of `NAME = "value"` pairs exported into every target command. Names must be valid shell identifiers, and pekit reserves the `PEKIT_` prefix — you cannot set a `PEKIT_*` variable here. See [Environments and keyrings](~pekit/recipes/environments-and-keyrings).
- **`[wrap]`** — a single `command` that every target runs *inside*. The string must contain exactly one `{{command}}` placeholder, which pekit replaces with the target's script. Use it to enter a toolchain shell, a container, or a sandbox.
- **`[source]`** — declares where the source tree comes from: `[source.git]`, `[source.url]`, or `[source.local]`. Absent, the recipe builds against its own directory. Covered in [Sources](~pekit/recipes/sources).
- **`[delegate]`** — opt in to borrowing `build`, `env`, `wrap`, or `packages` behaviour from a `pekit.toml` found inside the fetched source tree (or `delegate = true` for all of it).
- **`[build]` / `[test]` / `[install]` / `[clean]`** — the target sections. See below.

## Targets are shell commands

Each of `build`, `test`, `install`, and `clean` defines one or more **targets**. A target is fundamentally a shell command plus a little scheduling metadata:

- **`command`** *(required)* — the command to run. A **string** is executed with `sh -euc` (POSIX shell, with `-e` abort-on-error and `-u` unset-variable-is-error). An **array of strings** is executed directly as a program and arguments, without a shell, unless a wrapper is in play.
- **`needs`** — a list of other target names in the same section to stage first. Each named build a target needs is exposed to it as `PEKIT_<NAME>_OUT` (see below).
- **`clear_out`** — whether pekit wipes this target's staging directory before running (default `true`).
- **`dependencies`** — *(build targets only)* package dependencies to resolve and expose to the build. See [Dependencies and claims](~pekit/recipes/dependencies-and-claims).

A section can be written in **bare** form, with the keys directly under it (an implicit target named `main`):

```toml
[build]
command = "make"
```

…or in **named** form, one subtable per target:

```toml
[build.main]
command = "make"

[build.docs]
command = "make man"
needs = ["main"]
```

The two forms cannot be mixed within one section: a bare `[build]` with a `command` may not also carry a `[build.docs]` subtable.

### The `PEKIT_*` environment contract

This is the key interface between pekit and your build scripts. Before running a target, pekit stages a directory for it and exports a set of `PEKIT_*` variables describing where everything is. Your `command` reads them as ordinary shell variables — `$PEKIT_OUT`, `$PEKIT_VERSION`, and so on. **The build writes its artifacts into `$PEKIT_OUT`; that staged directory is what the package files later draw from.**

The target command runs with its working directory set to the source root (`$PEKIT_SOURCE_ROOT`) — except `clean`, which runs in the recipe directory.

| Variable | Meaning | When set |
|---|---|---|
| `PEKIT_OUT` | This target's own staging directory. Write your build output here. | Every target |
| `PEKIT_RECIPE_ROOT` | Directory containing `pekit.toml`. | Every target |
| `PEKIT_SOURCE_ROOT` | Root of the source tree the command runs in (its working directory). Equals the recipe root when there is no external source. | Every target |
| `PEKIT_LITERAL_ROOT` | The literal on-disk root of the fetched source checkout. Normally identical to `PEKIT_SOURCE_ROOT`. | Every target |
| `PEKIT_ROOT` | Working base for this source under `out_dir` — the parent of the per-target staging dirs. | Every target |
| `PEKIT_OUT_BASE` | The resolved `out_dir` base directory. | Every target |
| `PEKIT_COMMAND` | The command being run: `build`, `test`, `install`, or `clean`. | Every target |
| `PEKIT_TARGET` | The target's name (e.g. `main`). | Every target |
| `PEKIT_BUILD_TIMESTAMP` | The invocation's start time, as a Unix timestamp. | Every target |
| `PEKIT_SOURCE_TIMESTAMP` | The source tree's timestamp (e.g. the commit time), as a Unix timestamp. Useful for reproducible builds. | Every target |
| `PEKIT_WORKSPACE_ROOT` | The workspace root, or empty string when the recipe is not part of a workspace. | Every target (empty if none) |
| `PEKIT_VERSION` | The full resolved version string being built. | When a version is resolved (`build`/`test`/`install`; absent for `clean`) |
| `PEKIT_VERSION_MAJOR` `_MINOR` `_PATCH` `_PRERELEASE` `_BUILDMETA` | The parsed components of `PEKIT_VERSION`. | Same as `PEKIT_VERSION` |
| `PEKIT_<NAME>_OUT` | The staging directory of build target `<NAME>` named in this target's `needs`. `<NAME>` is upper-cased with `-` and `.` turned into `_`. | Per entry in `needs` |

`env.pekit.toml` and keyring files layer more variables on top (`PEKIT_KEYRING_*`, plus any user env), but the table above is the contract pekit guarantees. User-set `[env]` values never override a `PEKIT_*` variable — that prefix is reserved.

### Shell variables, not templates

Inside a target `command` you use **shell** variables: `$PEKIT_OUT`, `$PEKIT_VERSION`. Pekit does **not** run its own templating over commands — they are handed to the shell verbatim (after the `PEKIT_*` exports are prepended). The `{{...}}` syntax you see in fields like `source.git.ref = "{{version}}"` is a separate, **declarative** template mechanism that applies to specific recipe *fields*, not to shell commands. Keep the two straight: declarative fields template with `{{...}}`; shell commands read `$PEKIT_*`. See [Versions](~pekit/recipes/versions) for the declarative side.

## How pekit finds the recipe

By default pekit walks **up** from the current working directory looking for `pekit.toml`, stopping at the first one it finds (the same upward search then looks for a `workspace.pekit.toml` above it). So running a pekit command anywhere inside a recipe tree finds the right recipe.

You can override this:

- `--recipe <path>` points at a specific `pekit.toml` (or a directory containing one).
- A **remote locator** — a `github.com/...` path, a `.git` URL, or a `scheme://...` URL, optionally with a `@ref` and a `//subdir` — makes pekit clone the recipe from a git remote before running it.

The full flag and locator surface is on the [invocation](~pekit/using-pekit/invocation) page.

## Where to go next

- [Sources](~pekit/recipes/sources) — the `[source]` section in depth.
- [Package files](~pekit/recipes/packages) — turning `$PEKIT_OUT` into `.peipkg` payloads.
- [Recipe format reference](~pekit/reference/recipe-format) — the exhaustive `pekit.toml` schema.

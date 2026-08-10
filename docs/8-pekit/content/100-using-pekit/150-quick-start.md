---
title: Quick start
type: how-to
description: Build and package a tiny "hello" program with pekit from an empty directory — a minimal pekit.toml, one pekit build, and a .peipkg you can inspect.
related:
  - pekit/using-pekit/overview
  - pekit/using-pekit/commands-and-targets
  - pekit/recipes/anatomy
  - pekit/recipes/packages
---

This page takes you from an empty directory to a working `.peipkg` in about five minutes. You will write a two-file recipe, run `pekit build`, inspect the staged output, then run `pekit package` and look inside the artifact it writes. At the end you have a complete, minimal recipe you can grow into a real one.

## Prerequisites

- **A `pekit` binary on your `PATH`.** Pekit is a single binary built from its source repository with `go build ./cmd/pekit`; there is no separate installer. Note that pekit has [no `--help` or version banner](~pekit/using-pekit/invocation) — the docs are the manual.
- **A POSIX shell** (`sh`). Target commands run under `sh -euc`; any Linux system has this.
- **`zstd` and `tar`**, for the final inspection step only.

## Create the recipe

A recipe is a directory, and only one file in it is required: `pekit.toml`. Make a directory and write the recipe:

```console
$ mkdir hello && cd hello
```

```toml
# hello/pekit.toml
out_dir = "out"

[build]
command = '''
mkdir -p "$PEKIT_OUT/bin"
printf '#!/bin/sh\necho "Hello from Peios"\n' > "$PEKIT_OUT/bin/hello"
chmod +x "$PEKIT_OUT/bin/hello"
'''
```

Two things are going on here:

- **`out_dir`** names the directory pekit manages, relative to the recipe. Everything pekit stages or writes lands under it, and `pekit clean` may remove it wholesale — keep nothing precious there.
- **`[build]`** in this bare form defines a single build target named `main`. Its `command` is an ordinary shell script; pekit runs it with a set of `PEKIT_*` environment variables exported, of which the important one is `$PEKIT_OUT` — the target's own staging directory. **A build's job is to put its artifacts in `$PEKIT_OUT`.** Here the "build" just writes a shell script; a real recipe would run `make`, `cargo build`, or similar and copy the results in.

This recipe has no `[source]` section, so it builds against its own directory. Fetching real source trees is covered in [Sources](~pekit/recipes/sources).

## Run the build

From `hello/` (or any directory beneath it — pekit walks upward to find the nearest `pekit.toml`):

```console
$ pekit build
```

You should see three timestamped lines, ending in success:

```text
[14:30:01] [build] loaded recipe
[14:30:01] [main] running target
[14:30:01] [main] target succeeded
```

Nothing else prints because the build command itself is silent; anything your build writes to stdout or stderr is streamed through with a `[build:main]` prefix. Pekit exits `0` on success and `1` on any error.

## Inspect the staged output

Each build target stages into `out/build/<target>/`. Look at what the run produced:

```console
$ find out -type f
```

```text
out/.pekit/dependencies/build.main.json
out/build/main/bin/hello
```

`out/build/main/` is target `main`'s `$PEKIT_OUT`, and it now holds exactly what the command wrote (the `out/.pekit/` entry is pekit's own bookkeeping). This staged tree is what packaging draws from. The script even runs:

```console
$ out/build/main/bin/hello
Hello from Peios
```

## Describe the package

Packaging is declared in a second file beside the recipe. Write `hello/package.pekit.toml`:

```toml
# hello/package.pekit.toml
format = "peipkg"

[package]
name = "hello"
version = "0.1.0-1"
architecture = "noarch"
description = "A friendly greeting."
license = "MIT"

[files]
":bin/hello" = "usr/bin/hello"
```

The `peipkg` format requires `[package].version` and `[package].architecture`; the rest of the metadata is optional. The `[files]` table maps sources to destinations: the left side `":bin/hello"` is a build ref meaning "`bin/hello` from build target `main`'s staged output", and the right side is where the file lands inside the package. Destinations must sit under the peipkg layout's permitted top levels (`usr/bin/`, `usr/share/`, `etc/`, and so on) — see [Packaging files](~pekit/recipes/packages).

## Write the package

```console
$ pekit package
```

`package` stages the builds the package needs (re-running `build.main`), then writes the artifact:

```text
[14:31:12] [package] loaded recipe
[14:31:12] [main] running target
[14:31:12] [main] target succeeded
[14:31:12] [main] wrote package: /home/you/hello/out/package/main-e33807f0ae9abdc7/hello_0.1.0-1_noarch.peipkg
```

The artifact is named `<name>_<version>_<architecture>.peipkg` and lands in a per-package stage directory under `out_dir` (the hash in the directory name is derived from the package's identity). Add `--dry-run` to any command to see this plan without writing anything.

## Look inside

A `.peipkg` is a Zstandard-compressed tar archive: reserved `.peipkg/` metadata entries followed by the payload as it will be installed.

```console
$ zstd -d --stdout out/package/main-*/hello_0.1.0-1_noarch.peipkg | tar tf -
```

```text
.peipkg/manifest.json
.peipkg/files.json
usr/
usr/bin/
usr/bin/hello
```

That file is a real package: [peipkg](~peios/package-management/overview) can install it, and `pekit publish` can copy it to a configured destination. To start over, `pekit clean` removes the whole `out/` directory.

## Where to go next

- [Anatomy of a recipe](~pekit/recipes/anatomy) — every file in the recipe directory, all of `pekit.toml`'s sections, and the full `PEKIT_*` environment contract.
- [Commands and targets](~pekit/using-pekit/commands-and-targets) — the commands, named targets, `needs` ordering, target selection, and the `gen`/`verify` source-generation pair.
- [Invocation and flags](~pekit/using-pekit/invocation) — the command line: `--dry-run`, `--json`, and how recipes are located.
- [Recipe format reference](~pekit/reference/recipe-format) — the exhaustive schema for `pekit.toml` and package files.

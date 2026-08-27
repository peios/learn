---
title: What is pekit
type: concept
description: Pekit is the recipe-driven build and packaging tool for Peios. It reads declarative recipes, plans the work, then builds, tests, packages, signs, and publishes.
related:
  - pekit/running/commands-and-targets
  - pekit/running/invocation
  - pekit/recipes/anatomy
  - peios/package-management/composing-a-root
---

**Pekit** is the tool that turns source into packages. You describe a piece of software once — where its source comes from, how to build it, and how to split the result into `.peipkg` files — in a set of declarative **recipe** files, and pekit does the rest: fetches the source, selects versions, runs the build, stages the output, and writes packages you can install or publish.

Everything in the Peios tree is built with pekit. The kernel, the registry store, the init system, the package manager itself — each is a recipe, and `pekit package` produces the `.peipkg` files that [peipkg-compose](~peios/package-management/composing-a-root) and [peiso](~peios/building-images/overview) assemble into a running system.

## The one idea: plan before execute

Pekit's guiding principle is **predictability**. Every command declares exactly which flags it accepts, every source declares what it can do, and every build is planned before any side effect happens. Before pekit clones a repository, runs a shell command, or writes a package, it has already resolved which recipe is selected, which source tree is needed, which versions apply, which build targets will run, and which artifacts will be produced.

That plan is inspectable. Add [`--dry-run`](~pekit/running/invocation) to any command and pekit builds the same plan it would execute, prints it, and stops — no clones, no downloads, no writes. Strictness is the other half of the same idea: unknown flags, unknown recipe keys, and flags a command does not support are **errors**, caught up front, not halfway through a build.

## The pipeline

A single invocation runs through a fixed sequence:

```text
argv
  → invocation        parse and validate flags against the command
  → recipe            locate and load the recipe (walking up from the cwd)
  → versions          resolve the version selector into concrete versions
  → source            materialise the source tree for each version
  → delegation        merge any behaviour borrowed from the source tree
  → execute           run targets, or stage builds and write packages
  → artifacts         staged output and .peipkg files under out_dir
```

`build`, `package`, and `publish` may run this for **several versions** at once; `test` and `install` require the selector to resolve to exactly one. `clean`, `gen`, and `verify` skip the version and source stages entirely — they operate on the recipe directly.

## The shape of a recipe

A recipe is a directory. At minimum it holds one file:

```text
mypkg/
├── pekit.toml                 # the recipe: source, build/test/install/clean targets, env
├── package.pekit.toml         # what to package: files, symlinks, dependencies, metadata
├── packages.pekit/            # (optional) extra package members for multi-package recipes
├── env.pekit.toml             # (optional) reusable environment / wrapper definitions
└── prod.keyring.pekit.toml    # (optional) named keyring for signing and secrets
```

`pekit.toml` is the recipe proper — it declares the [source](~pekit/recipes/sources), the [build/test/install/clean targets](~pekit/running/commands-and-targets), and shared [environment](~pekit/recipes/environments-and-keyrings). The [package files](~pekit/recipes/packages) describe how staged build output is mapped into one or more `.peipkg` payloads. A [`workspace.pekit.toml`](~pekit/running/workspaces) one level up turns a directory of recipes into a **workspace** that pekit can drive as a unit.

The [Anatomy of a recipe](~pekit/recipes/anatomy) page walks through every file; the [recipe format reference](~pekit/reference/recipe-format) is the exhaustive schema.

## The commands

Ten commands, each with a defined job:

| Command | What it does |
|---|---|
| `build` | Run build targets and their build dependencies. |
| `test` | Stage the builds a test needs, then run test targets. |
| `install` | Stage the builds an install needs, then run install targets. |
| `package` | Stage builds and write `.peipkg` package artifacts. |
| `publish` | Package, then publish the artifacts to a configured destination. |
| `clean` | Run a clean target and/or remove pekit's managed output directory. |
| `gen` | Run source-generating targets that write generated source into the tree. |
| `verify` | Run gen targets' drift checks without writing anything. |
| `lock` | Fetch and pin source inputs in `pekit.lock` without building. |
| `workspace` | Run any of the above across every member of a workspace. |

The [Commands and targets](~pekit/running/commands-and-targets) page covers what each command selects, its version behaviour, and how target selection works.

## Where pekit fits

Pekit is the **producer-side build tool**. It stops at the `.peipkg` file. What happens next is other tools' work:

- [**peipkg**](~peios/package-management/overview) installs `.peipkg` files onto a live system.
- [**peipkg-compose**](~peios/package-management/composing-a-root) assembles a set of packages into an offline package root.
- [**peiso**](~peios/building-images/overview) turns a composed root into a bootable image.

Pekit produces packages in the [peipkg format](~peios/package-management/overview) and understands peipkg concepts directly: recipes declare package **dependencies**, automatic **ELF dependencies** are scanned from built binaries, and packages can declare the shared-name **claims** they participate in. See [Dependencies and claims](~pekit/recipes/dependencies-and-claims).

Pekit also carries the supply-chain half of producing packages: fetched sources are pinned trust-on-first-use in a lockfile, upstream release signatures can be verified against committed keys, artifacts are Ed25519-signed, binaries can be PIP-signed for the kernel, and every manifest records the provenance of its inputs, recipe, and builder. See [Signing and provenance](~pekit/running/signing-and-provenance).

> [!IMPORTANT]
> **Pekit supersedes the old `peipkg-build` recipe system.** Earlier Peios used a `peipkg.toml` + `build.sh` recipe built by a separate `peipkg-build` binary. Pekit replaces that entirely; a pekit recipe (`pekit.toml` + package files) is the current and only supported way to build a package. Documentation describing `peipkg-build` and its `build.sh` recipes is legacy.

## What to know before you start

A few facts about the tool as it ships today:

- **No `--help` yet.** Pekit does not currently print usage text. This page and the [invocation reference](~pekit/running/invocation) are the manual; the complete flag surface is tabulated in the [command-line reference](~pekit/reference/cli).
- **Exit status is 0 or 1.** Pekit exits `0` on success and `1` on any error. It does not use finer exit codes.
- **Events go to stdout.** Pekit's own events print as timestamped lines on stdout (structured JSON with [`--json`](~pekit/running/invocation)); a target's output streams through on its original stdout and stderr, and fatal errors go to stderr.

## Where to start

To learn the recipe format, begin with [Anatomy of a recipe](~pekit/recipes/anatomy) and follow the recipes section in order.

To use pekit against an existing recipe, read [Commands and targets](~pekit/running/commands-and-targets) and [Invocation and flags](~pekit/running/invocation).

For the exhaustive schema and CLI surface, the [reference section](~pekit/reference/recipe-format) has one page per file format plus the full command-line reference.

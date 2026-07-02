---
title: Commands and targets
type: reference
description: "Reference for pekit's command surface: the seven commands, what each selects, its version behaviour, and how build/test/install/clean targets are named, selected, and ordered by their build dependencies."
related:
  - pekit/using-pekit/overview
  - pekit/using-pekit/invocation
  - pekit/recipes/versions
  - pekit/recipes/multi-package
  - pekit/recipes/dependencies-and-claims
  - pekit/workspaces/workspaces
---

Every pekit invocation names exactly one **command**. The command decides three
things up front, before any side effect: which flags are legal, how many
versions the run may cover, and which **targets** in the recipe are selected and
in what order. This page is the reference for that surface.

For the flags themselves (how they parse, global flags like `--dry-run`), see
[Invocation and flags](~pekit/using-pekit/invocation). For version selectors
(`--version`, `--latest`, `--all-versions`), see [Versions](~pekit/recipes/versions).

## The seven commands

| Command | Selects | Versions | `--all` | Side effects |
|---|---|---|---|---|
| `build` | `build` targets + their `needs` | multiple | no | Runs build targets; stages their output under `out_dir`. |
| `test` | `test` targets + the builds they need | **single resolved** | no | Stages needed builds, then runs the selected test targets. |
| `install` | `install` targets + the builds they need | **single resolved** | no | Stages needed builds, then runs the selected install targets. |
| `package` | package members + the builds they list | multiple | yes | Stages builds and writes `.peipkg` artifacts under `out_dir`. |
| `publish` | package members (as `package`) | multiple | yes | Packages, then publishes to a configured `localdir` destination. |
| `clean` | one optional `clean` target | none | no | Runs a clean target and/or removes the managed output directory. |
| `workspace` | a delegated command across members | (delegated) | (delegated) | Runs one of the above across every workspace member. |

`workspace` is a wrapper: it parses a delegated command after its own flags and
runs it for each member. Its capabilities are exactly the delegated command's.
See [Workspaces](~pekit/workspaces/workspaces).

### Version behaviour

`build`, `package`, and `publish` iterate over **every** version the selector
resolves to, running the whole plan once per version. `test` and `install`
require the selector to resolve to a **single** version; if more than one
resolves, pekit stops before doing any work:

```text
invalid_version_selector: test requires a single resolved version
```

`clean` never resolves versions or materialises a source tree — it operates on
the recipe's declared output directory directly, so version-selection flags are
not accepted (see the capability matrix below).

### Command / capability matrix

Each command accepts a fixed set of flag groups. Passing a flag the command does
not support is an **error** up front (`unsupported_flag`), unless you pass
`--allow-unused`, which downgrades it to a suppressed warning.

| Flag group (flags) | build | test | install | package | publish | clean |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| version selection (`--version`, `--latest`, `--all-versions`) | ✓ | ✓ | ✓ | ✓ | ✓ | |
| local source (`--local`, `--prefer-local`) | ✓ | ✓ | ✓ | ✓ | ✓ | |
| `--no-build` | ✓ | ✓ | ✓ | ✓ | ✓ | |
| `--env` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--keyring` (`--keyring.<path>=…`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `--refresh-source` | ✓ | ✓ | ✓ | ✓ | ✓ | |
| `--allow-unanchored` | | | | | ✓ | |
| `--all` | | | | ✓ | ✓ | |
| clean mode (`--output-only`, `--target-only`) | | | | | | ✓ |

Global flags (`--dry-run`, `--quiet`, `--verbose`, `--json`, `--recipe`,
`--allow-unused`) are accepted by every command and are covered in the
[invocation reference](~pekit/using-pekit/invocation).

## The target model

`build`, `test`, `install`, and `clean` each read a same-named section from the
recipe. A section holds one or more **targets**, and a target is a shell command
plus optional metadata.

### Bare (`main`) targets

A bare section — with a `command` key directly on it — defines a single target
named `main`:

```toml
[build]
command = "make -j$(nproc)"

[test]
command = "make check"
```

`pekit build` with no selector runs `build.main`; `pekit test` runs `test.main`.
The keys allowed directly on a bare section are `command`, `needs`, `clear_out`,
and (for `[build]` only) `dependencies`.

### Named targets

Give a section sub-tables to define **named** targets, `[<command>.<name>]`:

```toml
[build.lib]
command = "make lib"

[build.tools]
command = "make tools"
needs    = ["lib"]
```

A target name must be a canonical selector: one or more of the characters
`A-Z a-z 0-9 _ . + -`, and it may not start with `-` or contain `/` or `:`. An
invalid name is rejected at load time (`invalid_selector`).

### Bare and named cannot mix

Within one section you use **either** the bare form **or** named sub-tables,
never both. Putting a `command` key on the section and also adding a sub-table
that is not a recognised target key is an error:

```text
mixed_targets: cannot mix bare [build] target with named [build.foo]
```

## Target selection

When you name selectors (positional arguments, or arguments after `--`), pekit
selects exactly those targets; each must exist in the section or the run fails:

```bash
pekit build lib tools
```

```text
missing_target: unknown build target "libz"; available targets: lib, tools
```

With **no** selector, selection follows these rules for the command's section:

| Situation | Result |
|---|---|
| Section has a `main` target | `main` is selected. |
| No `main`, command is `build`, exactly one target exists | that lone target is selected. |
| No `main`, and none of the above | error, listing the available targets. |
| Section is absent / empty | `missing_target: recipe has no <command> targets`. |

The single-target fallback is **build-only**. For `test` and `install`, a bare
`pekit test` with no `test.main` and multiple test targets is ambiguous:

```text
ambiguous_target: no test.main target; available targets: fast, full
```

## Build dependencies (`needs`)

A target's `needs` lists **build** target names that must be staged first.

- For `build`, the selected targets and everything reachable through `needs` are
  gathered and run in **dependency order** (a target runs after everything it
  needs). Each build runs at most once per invocation.
- For `test`, `install`, and `package`, pekit pulls the build targets named in
  the selected target's `needs` (for `package`, the `builds` list on the package
  member), stages those builds first in dependency order, then runs the selected
  test/install targets (or writes packages).

A `needs` entry that does not name an existing build target is an error:

```text
missing_target: test.full needs missing build target "core"
```

Dependency edges form a DAG. A cycle is detected and reported with the path:

```text
target_cycle: build dependency cycle: a -> b -> a
```

`--no-build` may name already-staged build targets to skip re-running them;
naming a build target that does not exist is likewise a `missing_target` error.

## `clean`

`clean` has two independent effects, gated by two mutually exclusive mode flags:

| Invocation | Runs clean target | Removes output dir |
|---|:---:|:---:|
| `pekit clean` (default) | yes, if `clean.main` (or the named selector) exists | yes |
| `pekit clean --output-only` | no | yes |
| `pekit clean --target-only` | yes | no |

Details:

- **Default.** Runs `clean.main` if present (if there is no `clean.main` and no
  selector, the target step is simply skipped — not an error), then removes the
  recipe's managed output directory (`out_dir`).
- **`--output-only`.** Removes the output directory only; no target runs. Because
  no target runs, `--env` and `--keyring` are unused and rejected
  (`unsupported_flag`), unless `--allow-unused` downgrades them to warnings.
- **`--target-only`.** Runs the clean target only; the output directory is left
  in place. With no `clean.main` and no explicit selector this is an error:
  `missing_target: --target-only requires clean.main or an explicit clean target`.

`clean` accepts **at most one** target selector; more than one is rejected:

```text
invalid_selector: clean accepts at most one target selector
```

`--output-only` and `--target-only` cannot be combined.

## `--all` for `package` and `publish`

A multi-package recipe has several package **members**. `package` and `publish`
select members the same way targets are selected — by naming them, with an
optional `:instance` suffix for [multi-package](~pekit/recipes/multi-package)
enum instances — with two conveniences:

- With no selector and a single member, that member is used; with no selector and
  multiple members, the run is ambiguous and lists the members.
- `--all` selects **every** member.

`--all` is exclusive with explicit selectors:

```text
invalid_flags: --all cannot be combined with package selectors
```

On any command other than `package` or `publish`, `--all` is an unsupported flag.

## Selector rules

Selectors are the command's positional arguments plus everything after a `--`
separator. Two rules apply to all of them:

- A selector may **not** start with `-`. A leading dash makes pekit treat the
  value as a (probably mistyped) flag; put it after `--` instead:

  ```text
  invalid_selector: selector "-lib" starts with '-'; use -- before selector-like values
  ```

  ```bash
  pekit build -- -lib
  ```

- Target selectors must be canonical (`A-Z a-z 0-9 _ . + -`, no leading `-`, no
  `/` or `:`). Package selectors follow the same grammar but allow a single `:`
  to separate a member from an enum instance.

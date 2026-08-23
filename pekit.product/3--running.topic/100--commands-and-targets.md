---
title: Commands and targets
type: reference
description: "The commands, what each selects and its version behaviour, target naming and needs ordering, and the gen/verify source-generation pair."
related:
  - pekit/getting-started/what-is-pekit
  - pekit/running/invocation
  - pekit/reference/cli
  - pekit/recipes/versions
  - pekit/recipes/multi-package
  - pekit/recipes/dependencies-and-claims
  - pekit/running/workspaces
---

Every pekit invocation names exactly one **command**. The command decides three
things up front, before any side effect: which flags are legal, how many
versions the run may cover, and which **targets** in the recipe are selected and
in what order. This page is the reference for that surface.

For the flags themselves (how they parse, global flags like `--dry-run`), see
[Invocation and flags](~pekit/running/invocation). For version selectors
(`--version`, `--latest`, `--all-versions`), see [Versions](~pekit/recipes/versions).

## The commands

| Command | Selects | Versions | `--all` | Side effects |
|---|---|---|---|---|
| `build` | `build` targets + their `needs` | multiple | no | Runs build targets; stages their output under `out_dir`. |
| `test` | `test` targets + the builds they need | **single resolved** | no | Stages needed builds, then runs the selected test targets. |
| `install` | `install` targets + the builds they need | **single resolved** | no | Stages needed builds, then runs the selected install targets. |
| `package` | package members + the builds they list | multiple | yes | Stages builds and writes `.peipkg` artifacts under `out_dir`. Recipes with a reproducible source also emit a [corresponding-source package](~pekit/recipes/sources#source-packages). |
| `publish` | package members (as `package`) | multiple | yes | Packages, then publishes to a configured `localdir` destination. |
| `clean` | one optional `clean` target | none | no | Runs a clean target and/or removes the managed output directory. |
| `gen` | `gen` targets | none | yes | Runs gen commands; writes generated source **into the tree**. |
| `verify` | `gen` targets | none | yes | Runs gen `verify_command`s; a read-only drift check (writes nothing). |
| `lock` | the recipe's source | multiple | no | Fetches and pins the selected versions in [`pekit.lock`](~pekit/recipes/sources#the-lockfile) without building. With no version flags, reports the current lock instead. |
| `workspace` | a delegated command across members | (delegated) | (delegated) | Runs one of the above across every workspace member. |

`gen` and `verify` are the source-generating pair — see
[Generating source](#generating-source-gen-and-verify) below. The rest of this
page's target model applies to `build`/`test`/`install`/`clean`; `gen` targets
have their own shape.

`workspace` is a wrapper: it parses a delegated command after its own flags and
runs it for each member. Its capabilities are exactly the delegated command's.
See [Workspaces](~pekit/running/workspaces).

### Version behaviour

`build`, `package`, `publish`, and `lock` iterate over **every** version the
selector resolves to, running the whole plan once per version. `test` and `install`
require the selector to resolve to a **single** version; if more than one
resolves, pekit stops before doing any work:

```text
invalid_version_selector: test requires a single resolved version
```

`clean`, `gen`, and `verify` never resolve versions or materialise a source
tree — they operate on the recipe directly (the output directory, or the
committed tree at the recipe root), so version-selection flags are not accepted
(see the capability matrix below).

### Command / capability matrix

Each command accepts a fixed set of flag groups. Passing a flag the command does
not support is an **error** up front (`unsupported_flag`), unless you pass
`--allow-unused`, which downgrades it to a suppressed warning. Broadly:
`build`, `test`, `install`, `package`, and `publish` share the version-selection,
local-source, `--no-build`, `--no-verify`, and `--refresh-source` groups; `--all`
is `package`/`publish`/`gen`/`verify` only; `--allow-unanchored` and `--allow-unsigned` are `publish`
only; `clean` takes only `--env`, `--keyring`, and its own mode flags
(`--output-only` / `--target-only`); `gen` and `verify` take only `--env`,
`--keyring`, and `--all`; `lock` takes version selection, `--refresh-source`,
and its own `--repin`. The full command-by-flag matrix is in the
[command-line reference](~pekit/reference/cli).

Global flags (`--dry-run`, `--quiet`, `--verbose`, `--json`, `--recipe`,
`--allow-unused`) are accepted by every command and are covered in the
[invocation reference](~pekit/running/invocation).

## The target model

`build`, `test`, `install`, and `clean` each read a same-named section from the
recipe. A section holds one or more **targets**, and a target is a shell command
plus optional metadata. (`gen` targets live in a `[gen.*]` section too, but have
a different shape — [see below](#generating-source-gen-and-verify).)

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

## Generating source (`gen` and `verify`)

Some recipes have source that is **generated** and committed to the tree —
language bindings from a canonical header, a table baked from a schema, a file
derived from another. That is not a build: a build reads source and writes
artifacts under `out_dir`; a generator reads canonical inputs and writes
generated source *back into the tree*. pekit models it as a separate command,
`gen`, with a matching drift check, `verify`.

A `gen` target runs at the recipe root and its product is the files it writes
in-tree. Its `$PEKIT_OUT` is a pekit-managed **scratch** directory
(`<out_dir>/.scratch/gen/<name>`, cleaned on success, kept on failure) that sits
outside the artifact area — packaging and `--no-build` reuse never see it. It is
a handy place for a `verify_command` to regenerate into.

```toml
[gen.bindings]
# Runs at the recipe root; writes generated source in place.
command = "./tools/gen-bindings.sh"

# Optional drift gate. Exit 0 = in sync, non-zero = stale. It owns its own
# comparison — pekit never diffs for you and never assumes the generator is
# deterministic. A common shape regenerates into the scratch $PEKIT_OUT and
# diffs against the committed tree:
verify_command = """
./tools/gen-bindings.sh --out "$PEKIT_OUT/fresh"
diff -ru generated "$PEKIT_OUT/fresh"
"""

# Scope of the pre-flight (see below). Omit to gate every build/test.
verify_on_build = ["thing-that-embeds-bindings"]
verify_on_test  = []

[gen.bindings.dependencies.apt]
python3 = "*"
```

The keys allowed on a `[gen.<name>]` target are `command` (required),
`verify_command`, `verify_on_build`, `verify_on_test`, `dependencies`, and
`verify_dependencies`. Gen targets have **no** `needs` and no build DAG — they
are independent of the build chain. Bare `[gen]` means `gen.main`, exactly like
the other sections; `pekit gen --all` / `pekit verify --all` operate on every
gen target.

- **`pekit gen <name>`** runs `command` — regenerate in place.
- **`pekit verify <name>`** runs `verify_command` — check only, never writes the
  tree. This is the on-demand / CI drift gate. Naming a gen target that has no
  `verify_command` is an error. A bare `pekit verify` selects `gen.main`,
  exactly like the other commands; `pekit verify --all` runs every gen target
  that has a `verify_command`, and errors only when none does.

### Pre-flight drift checking

The point of `verify_command` is that a consuming command never proceeds from a
stale tree by accident. Before `build`, `test`, `install`, `package`, or
`publish` runs, pekit runs the drift gates **scoped to what that command will
do**, and fails fast if any is stale:

```text
gen_out_of_date: gen target "bindings" is out of date: ...
  fix:  pekit gen bindings
  skip: pekit build thing --no-verify=bindings
```

Scope is per namespace, and the two keys are separate because a `[build.x]` and
a `[test.x]` can share the bare name `x`:

| `verify_on_build` / `verify_on_test` | Meaning |
|---|---|
| **absent** | Gate **every** target in that namespace (the safe default). |
| **`[]`** (empty) | Gate **nothing** — the drift check runs only via `pekit verify`. |
| **`["a", "b"]`** | Gate only when target `a` or `b` in that namespace runs. |

A gen target's gate fires when its `verify_on_build` gates a build the command
will run, **or** its `verify_on_test` gates a test it will run. `package` and
`publish` gate conservatively against every build target (they run builds under
the hood, and the exact set depends on package resolution). Multiple stale gates
are collected and reported together, not one at a time.

Set `verify_on_build = []` for a generator whose output nothing builds (a
downstream SDK, say): leaving it absent would drag the generator's toolchain
into every unrelated build's pre-flight for no benefit. Use the scoped list
form when only some targets actually consume the generated output.

### `--no-verify` and `verify_dependencies`

`--no-verify` opts out of the pre-flight for one invocation:

- `pekit build --no-verify` skips **all** drift gates.
- `pekit build --no-verify=bindings,other` skips only the named gens (an unknown
  name is an error).
- On `package` / `publish`, `--no-verify` skips the same pre-flight — those
  commands gate conservatively against every build target, as above.

By default `verify_command` runs with the gen target's `dependencies`. If it
needs a *different* (usually smaller) toolchain — a cheap hash check rather than
a full regen — declare `[gen.<name>.verify_dependencies.*]`; when present it
**fully replaces** `dependencies` for the verify run.

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

## See also

- [Invocation and flags](~pekit/running/invocation) — the grammar, flag value forms, and global flags.
- [Command-line reference](~pekit/reference/cli) — the full command-by-flag capability matrix.
- [Versions](~pekit/recipes/versions) — the version selectors these commands accept.
- [Workspaces](~pekit/running/workspaces) — running a command across every member.

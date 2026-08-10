---
title: Workspaces
type: concept
description: "Driving many pekit recipes as one unit: the workspace.pekit.toml file, include/exclude member discovery, shared env/wrap/policy, the workspace command and its strict flag placement, member identity, the concurrent execution model with --jobs and --fail-fast, per-member strictness, and cross-member publish-destination collision detection."
related:
  - pekit/using-pekit/invocation
  - pekit/recipes/dependencies-and-claims
  - pekit/recipes/environments-and-keyrings
  - pekit/recipes/packages
  - pekit/reference/cli
  - pekit/reference/supporting-files
---

A **workspace** lets you drive a whole collection of recipes as one unit. Instead
of running `pekit build` in each recipe directory by hand, you declare which
recipes belong together in a `workspace.pekit.toml` file and run a single
`pekit workspace build`, which delegates that command to every member. This is
how a distro-scale tree of packages — dozens or hundreds of recipes — is built,
tested, packaged, and published in one go.

A workspace does three things:

1. **Discovers members** from `include`/`exclude` globs (each member is a
   directory containing a `pekit.toml`).
2. **Shares configuration** — `[env]`, `[wrap]`, and a distro-wide `[policy]` —
   down to every member.
3. **Schedules and delegates** a single command across all members, with
   optional concurrency, fail-fast, and cross-member safety checks.

## The `workspace.pekit.toml` file

The workspace file is TOML and lives at the root of the tree it governs. Its
schema is small — the loader (`LoadWorkspace`) accepts exactly five top-level
keys and rejects anything else with `unknown_key`: `include` and `exclude`
(globs selecting and removing member directories, relative to the workspace
root), `[env]` and `[wrap]` (shared configuration contributed to every member),
and `[policy]` (distro-wide derivation policy — see
[Policy](#policy-symbol-version-floors)). The key-by-key schema is in
[Supporting files](~pekit/reference/supporting-files).

`include` is mandatory: an omitted or empty `include` fails with `missing_key`
("workspace include is required"). Everything else is optional.

```toml
# workspace.pekit.toml at the distro root
include = ["core/*", "extra/**"]
exclude = ["extra/experimental/*"]

[env]
SOURCE_DATE_EPOCH = "1700000000"

[wrap]
command = ["nice", "-n", "10", "{{command}}"]

[policy.symbol_versions]
"libc.so.6" = "GLIBC_"
```

### Member discovery

`include` and `exclude` are glob patterns matched against the directory tree
under the workspace root. Matching uses **doublestar** globbing, so ordinary
wildcards (`*`, `?`, character classes) work and `**` matches across directory
boundaries. Patterns are always workspace-root-relative.

Discovery proceeds as:

1. Every `exclude` pattern is expanded and its matches recorded.
2. Every `include` pattern is expanded. A match is kept only if it was **not**
   excluded **and** the matched directory contains a `pekit.toml`.

A matched directory with no `pekit.toml` is silently ignored — it is simply not a
recipe, so it is not a member. This means you can point `include` at a broad glob
(`extra/**`) and only the directories that actually hold recipes become members.

If discovery yields no members at all, the run fails with `empty_workspace`
("workspace has no members").

> Members are recipe **directories**, identified by the presence of a
> `pekit.toml`. The workspace file itself is named `workspace.pekit.toml`; it is
> a different file from a recipe.

### Locating the workspace

When you run `pekit workspace`, pekit finds the workspace file by walking upward
from the current directory looking for `workspace.pekit.toml` (the same
`findUp` search recipes use). You can override this with `--workspace <path>`,
which accepts a path to a `workspace.pekit.toml` file, a directory containing
one, or a remote locator (for example a `github.com/...` reference).

## Member identity

Each member has a stable **id**: its workspace-relative directory path, written
with forward slashes (for example `core/zlib` or `extra/tools/ripgrep`). This id
is the member's name everywhere it appears:

- in diagnostics and error messages (`member_failed`, `member_skipped`);
- in structured JSON events and in output-line prefixes;
- in the publish-collision owner labels (see below);
- in the end-of-run summary.

Members are processed in a deterministic **order**: ids are sorted
lexicographically. With the default single-worker execution this is the exact
order members run in; with concurrency it is the order in which work is
dispatched.

## Invocation

```text
pekit [global flags] workspace [workspace flags] <command> [args and flags]
```

`workspace` is itself a command, but it does no building of its own — it
**delegates** another command (`build`, `test`, `install`, `package`,
`publish`, or `clean`) to every member. That delegated command and its arguments
come after the workspace flags.

### Strict flag placement

The tail after `workspace` is parsed specially (`parseWorkspaceTail`), and the
placement rules are strict:

- **Workspace flags — `--jobs N` and `--fail-fast` — must appear after
  `workspace` and before the delegated command.** They are recognised only in
  this slot.
- **Command-level flags** (version selection, `--local`, `--env`, `--keyring`,
  `--refresh-source`, `--all`, …) belong to the delegated command and must come
  **after** it. Placing one before the delegated command is an error with a
  hint: *"workspace command flag `<name>` must appear after the delegated
  command."*
- **Global flags** (`--dry-run`, `--quiet`, `--verbose`, `--json`,
  `--allow-unused`, `--workspace`) may appear either before `workspace` or in
  the tail before the delegated command.

```console
# correct: workspace flags before the command, command flags after
$ pekit workspace --jobs 4 --fail-fast build --version 1.2.3

# also correct: a global flag may precede workspace
$ pekit --dry-run workspace build

# error: --version is a command flag placed before the delegated command
$ pekit workspace --version 1.2.3 build
#   workspace command flag version selection must appear after the delegated command
```

Because `--jobs`/`--fail-fast` are recognised *only* in the workspace slot,
writing them after the delegated command hands them to the delegated command's
own parser, which rejects them as an `unknown_flag`. Keep them in the workspace
slot.

Both failures share the diagnostic code `missing_workspace_command`: it fires
when a command flag precedes the delegated command, and when no delegated
command follows the workspace flags at all ("workspace requires a delegated
command").

## Execution model

Each member is run as an ordinary **per-recipe invocation** of the delegated
command — exactly as if you had `cd`'d into that member and run
`pekit <command> ...` there, with the delegated flags and any positional
selectors carried through unchanged.

### Concurrency: `--jobs`

`--jobs N` sets how many members run concurrently. `N` must be a **positive
integer**; a missing value is `missing_flag_value` and a non-positive or
non-numeric value is `invalid_flag_value` ("--jobs requires a positive
integer"). The **default is 1**, i.e. members run one at a time in id order.

### Fail-fast: `--fail-fast`

By default the workspace attempts **every** member even if some fail: it runs
them all and then fails the overall command at the end if any member failed
(`workspace_failed`, "N workspace member(s) failed").

With `--fail-fast`, the first member failure sets a stop flag so that **no
further members are started**. Members that had not yet begun are recorded as
**skipped**.

> `--fail-fast` stops *starting* new members; it does **not** cancel members
> that are already running. In-flight members run to completion. There is no
> mid-member cancellation.

### No inter-member dependencies

Members are independent. Pekit does **not** compute a dependency graph between
members, does not topologically order them, and does not make one member's build
visible to another as an input. The only ordering is the lexicographic id order
used for dispatch. If a member needs another member's output, that relationship
must be expressed through the normal recipe machinery (sources, package
dependencies), not through workspace membership.

### Summary

At the end of a run pekit emits a `workspace_summary` event tallying members as
**succeeded**, **failed**, or **skipped**:

```text
12 succeeded, 1 failed, 3 skipped
```

*Succeeded* and *failed* count members that actually ran; *skipped* covers
members not started because of `--fail-fast`, and members skipped by selector
planning (below). The overall command exits non-zero if any member failed.

## Per-member strictness

The delegated command and its flags are validated once, when the tail is parsed.
Beyond that, strictness is evaluated **per member**, because members differ: one
recipe may define a `build` target or a package selector that another does not.

- Each member runs the delegated command against its own recipe. If a flag or
  selector cannot be honoured by that member's recipe, **that member errors** —
  its failure is reported (`member_failed`) and counted, and the other members
  are unaffected (unless `--fail-fast` is set).
- **`--allow-unused`** relaxes this per member. When a run carries positional
  selectors (target names, or `def:variant` package selectors) together with
  `--allow-unused`, pekit plans which selectors apply to which member
  (`planWorkspaceSelectors`):
  - selectors that a member cannot satisfy are **suppressed** for that member
    (reported via `workspace_selector_suppressed`);
  - a member to which **none** of the requested selectors apply is **skipped**
    ("no requested selectors apply to member");
  - if a requested selector applies to **no** member at all, the whole run
    fails with `missing_selector` ("workspace selector … matches no selected
    member").

  `--allow-unused` also suppresses per-member *unsupported version selection*
  rather than failing that member.

Without `--allow-unused`, selectors are passed to every member verbatim and a
member that does not recognise one fails in the usual way.

## Cross-member publish collision detection

When the delegated command is `publish`, two members could be configured to
publish an artifact to the **same destination** — a mistake that would have them
overwrite each other. Pekit catches this **before** publishing anything.

A **preflight** pass runs each member's publish planning in dry-run mode and
reserves every resolved destination path in a shared `DestinationRegistry`. The
registry keys destinations by path and records an **owner** of the form
`<member-id>:<instance>`. Reserving a path that a *different* owner already holds
fails the entire run with `publish_collision` ("publish destination collision
between … and …"). Reserving the same path for the same owner is idempotent, so a
member does not collide with itself.

Because this is a preflight, a destination clash is reported up front, before any
member has written to a publish target.

## Shared configuration

### `[env]` and `[wrap]`

`[env]` and `[wrap]` declared at the workspace level are shared defaults
contributed to **every** member, layered together with each member recipe's own
`[env]` and `[wrap]`. For how these compose with recipe- and environment-file
values — and the precedence between them — see
[Environments and keyrings](~pekit/recipes/environments-and-keyrings). The
`[wrap]` command follows the same `{{command}}` placeholder rules as a recipe
wrap.

### Policy: symbol-version floors

The `[policy]` table carries distro-wide derivation policy. Its one current
sub-table is `[policy.symbol_versions]`, a map from a shared-library **soname**
to the **symbol-version token prefix** whose tokens are commensurable with the
providing package's version:

```toml
[policy.symbol_versions]
"libc.so.6" = "GLIBC_"
"libstdc++.so.6" = "GLIBCXX_"
```

This governs which sonames receive a symbol-version floor when pekit derives a
package's dependencies across the workspace — so that, for example, a binary
using a `GLIBC_2.34` symbol gains an appropriate lower bound on its libc
dependency. An unknown sub-table under `[policy]` is rejected
(`unknown_key`, "policy.… is not a known policy table"). For how derived
dependencies and claims work, see
[Dependencies and claims](~pekit/recipes/dependencies-and-claims).

## Where to go next

For the recipes a workspace's members are, read [Anatomy of a recipe](~pekit/recipes/anatomy).

For how workspace `[env]` and `[wrap]` compose with a recipe's own, read [Environments and keyrings](~pekit/recipes/environments-and-keyrings).

For the full flag surface and remote locators, read [Invocation and flags](~pekit/using-pekit/invocation).

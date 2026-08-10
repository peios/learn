---
title: Invocation and flags
type: reference
description: "The pekit command line: grammar, flag value forms, the global execution flags (--recipe, --workspace, --allow-unused, --dry-run, --quiet, --verbose, --json), their mutual-exclusion rules, the output renderers, exit codes, and how a recipe is located including remote recipe locators."
related:
  - pekit/using-pekit/overview
  - pekit/using-pekit/commands-and-targets
  - pekit/reference/cli
  - pekit/workspaces/workspaces
  - pekit/recipes/sources
---

This page is the reference for pekit's command line: the grammar, how flag values
are written, the flags every command accepts, and how pekit decides which recipe
to run. For what each command does and how it selects targets, see
[Commands and targets](~pekit/using-pekit/commands-and-targets).

## Grammar

```text
pekit [global flags] <command> [args and flags]
pekit [global flags] workspace [workspace flags] <command> [args and flags]
```

There is exactly one command per invocation, drawn from `build`, `test`,
`install`, `package`, `publish`, `clean`, and `workspace`. Anything before the
command that is not a recognised flag is an error (`unknown_command` /
`unknown_flag`); a missing command is `missing_command`.

**Flags may appear before or after the command.** Pekit parses flags the same way
on both sides of the command word, so these are equivalent:

```console
$ pekit --dry-run build
$ pekit build --dry-run
```

The one structural exception is `workspace`, whose tail is parsed specially: the
`workspace`-only flags (`--fail-fast`, `--jobs`) must come *before* the delegated
command, and everything after the delegated command is parsed as an ordinary
invocation of that command. See [Workspaces](~pekit/workspaces/workspaces).

### `--` stops flag parsing

A bare `--` ends flag parsing. Every token after it is captured verbatim and
treated as a positional selector:

```console
$ pekit build -- ./tools ./libs
```

Positional selectors may not begin with `-`. A leading-`-` token before `--` is
read as a flag (and rejected as unknown if it is not one); after `--` it is still
rejected as a selector with the diagnostic *"use `--` before selector-like
values"*. Use `--` for selectors that merely *look* option-like (for example a
path), not to pass a selector that begins with a dash.

## Flag value forms

Flags fall into three shapes — **no-value**, **required-value**, and
**optional-value** — and the shape decides how a value may be written. Which
shape each flag takes is tabulated per flag in the
[command-line reference](~pekit/reference/cli); the rules are as follows.

**No-value flags** (`--dry-run`, `--json`, and the like) never take a value:
`--flag=x` is an error (`unexpected_flag_value`).

**Required-value flags** accept either the separated form (`--recipe path`) or the
`=` form (`--recipe=path`). With the separated form pekit consumes the next token
as the value — unless that token is missing, is `--`, or itself begins with `-`,
in which case the flag errors with `missing_flag_value`. With the `=` form an
empty value (`--recipe=`) is rejected the same way.

**Optional-value flags** take a value **only** through `=`. They never consume the
following token. So:

```console
$ pekit build --local              # --local with an empty value
$ pekit build --local=/src/mypkg   # --local with a value
$ pekit build --local /src/mypkg   # --local (empty) + /src/mypkg as a selector
```

`-V` is an alias for `--version` and behaves identically (it is a required-value
flag; it is *not* a version-print flag — pekit has no version banner and no
`--help`).

Per-key keyring values use a dotted-path form, `--keyring.<path>=<value>`, which
always requires the `=` and a non-empty path.

## Global flags

Seven flags are parsed in any position regardless of command: `--recipe`,
`--workspace`, `--allow-unused`, `--dry-run`, `--quiet`, `--verbose`, and
`--json`. Six are accepted by every command; the seventh, `--workspace`, is only
valid with the `workspace` command. Each is covered in its own section below,
and the [command-line reference](~pekit/reference/cli) tabulates all seven with
their value forms. The rest of pekit's flags (`--version`/`-V`, `--latest`,
`--local`, `--env`, `--keyring`, `--all`, and so on) are command-specific and
are covered on [Commands and targets](~pekit/using-pekit/commands-and-targets).

`--recipe <path|dir>` selects the recipe directly instead of searching upward
from the cwd (see [How a recipe is located](#how-a-recipe-is-located));
`--workspace <path|dir>` does the same for the workspace file.

### Mutual-exclusion rules

Validation rejects contradictory combinations up front, before any work runs:
`--quiet` cannot be combined with `--verbose` or `--json`; `--recipe` cannot be
combined with `--workspace` (and `--workspace` is rejected outside the
`workspace` command); the version selectors (`--version` / `--latest` /
`--all-versions`), the local-source flags (`--local` / `--prefer-local`), and
the clean modes (`--output-only` / `--target-only`) are each mutually exclusive
within their group. The complete validation table, with each diagnostic, is in
the [command-line reference](~pekit/reference/cli).

## `--allow-unused`

Every command declares which flags it accepts. Passing a **recognised** flag that
the effective command does not support is normally an error
(`unsupported_flag`), for example version selection on `clean`, or `--all` on
`build`. `--allow-unused` turns each such case into a non-fatal notice: pekit
records it and emits an `unused_suppressed` event at the start of the run instead
of aborting.

`--allow-unused` only relaxes the "recognised-but-unused" check. It does **not**
excuse:

- unknown flags (`unknown_flag`) or unknown commands (`unknown_command`);
- malformed flag values — missing values, empty `=` values, or `=value` on a
  no-value flag;
- the mutual-exclusion rules above;
- bad selectors (a selector beginning with `-`, or more selectors than the
  command accepts).

This is what lets you fan a shared set of flags across a whole
[workspace](~pekit/workspaces/workspaces) even when some members' commands ignore
some of the flags.

## `--dry-run`

`--dry-run` runs the same planning pipeline as a real invocation — it locates and
loads the recipe, resolves the version selector, and prepares source state — but
stops at every side-effecting boundary instead of crossing it. In place of the
action pekit emits a plan event:

- a target that would run emits `target_plan` ("would run target") and does not
  execute the command or touch the stage directory;
- `clean` that would delete managed output emits `clean_plan` ("would remove
  managed output") and removes nothing;
- `package` / `publish` emit their plan events rather than writing or shipping
  artifacts.

Use `--dry-run` to inspect exactly what a command would do. Combine it with
`--json` to get the plan as a single structured object (below).

## Output renderers

The renderer is chosen from the flags. `--json` selects the JSON renderer;
otherwise the human renderer is used, and `--quiet` puts it in quiet mode.

### Human (default)

Pekit's own events print as timestamped lines, `[15:04:05] message`, optionally
prefixed with a context tag (member, command, target, package, version) when the
event carries one. Live output from the targets pekit runs is streamed through
with a `[member target version]` prefix, preserving each line's original stream —
stdout stays on stdout, stderr stays on stderr. Fatal errors are written to
stderr.

### `--quiet`

Quiet mode keeps the human format but drops routine progress, emitting only
`warning`, `artifact`, `publish`, and `workspace_summary` events. Target output
is unaffected. `--quiet` cannot be combined with `--verbose` or `--json`.

### `--verbose`

Verbose mode adds extra events (such as per-target stage preparation) to the human
log. It is otherwise the human renderer.

### `--json`

`--json` emits newline-delimited JSON — one event object per line — to stdout, so
the run can be consumed by another program. Each object has a `type` and a
timestamp plus whatever context fields apply; target output arrives as
`target_output` events carrying the `stream` and `text`. Errors are emitted as an
`error` event.

`--dry-run --json` is special-cased: instead of streaming events, pekit buffers
them and, at the end, prints a **single** `plan` object:

```json
{"type":"plan","time":"...","command":"build","workspace":false,"events":[ ... ]}
```

The `events` array holds the buffered plan events; `command` is the effective
command and `workspace` is whether the run went through the `workspace` command.

## Exit codes

Pekit uses two exit codes only: `0` on success, `1` on any error — bad
invocation, missing recipe, failed build, and so on. There are no finer-grained
codes, and there is **no `--help` or `help` command**: this page,
[Commands and targets](~pekit/using-pekit/commands-and-targets), and the
[command-line reference](~pekit/reference/cli) are the manual.

## How a recipe is located

Pekit resolves exactly one recipe per (non-workspace) run:

1. **`--recipe <path|dir>`** — if given, this wins. A directory means
   `<dir>/pekit.toml`; a file path is used as-is. A missing target is
   `missing_recipe`.
2. **A remote positional** — if `--recipe` was not given and the first positional
   argument looks like a remote locator, it is taken as the recipe (and dropped
   from the selector list).
3. **Walking up** — otherwise pekit searches from the current directory upward
   for the nearest `pekit.toml`, stopping at the filesystem root
   (`not_found` if none is found).

Once the recipe root is known, and unless `--workspace` was supplied, pekit also
walks upward from that root for a `workspace.pekit.toml`; if one is found the
recipe is treated as a member of that workspace.

### Remote recipe locators

A **remote locator** is a recipe reference that points at a git repository rather
than a local path. A value is treated as remote when it does *not* start with `.`
or `/` and it either begins with `github.com/`, contains `://`, ends with `.git`,
or contains a `//` subdirectory separator. Examples:

```console
$ pekit build github.com/acme/tools
$ pekit build github.com/acme/tools//subdir@v1.2.0
$ pekit build https://git.example.org/acme/tools.git//pkg@main
```

The locator may carry a `//subdir` to select a directory inside the repository and
an `@ref` (branch, tag, or commit) to pin a revision. When pekit sees a remote
locator — whether as the positional or as the value of `--recipe` — it
**materialises** it: it mirror-clones the repository into a per-user cache under
the system temp directory (fetching updates if already cached), checks out the
resolved commit into a clean working tree, and then treats the checkout (plus any
`//subdir`) as the recipe root. From there the run proceeds exactly as it would
for a local recipe.

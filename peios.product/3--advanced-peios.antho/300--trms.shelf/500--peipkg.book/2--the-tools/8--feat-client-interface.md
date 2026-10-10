---
title: feat client interface
description: Feature state storage, query JSON and driven-mode events for clients that run feat alongside peipkg.
---

`feat` is a separate feature tool, not a package transaction verb. This
reference keeps its client-facing state and protocol details together with
the [peipkg driven protocol](~peios/peipkg/the-tools/the-driven-mode) it uses.
For human-operated commands and interrupted-feature recovery, see
[Using feat](~peios/features/using-feat).

## Where its state is kept

A feature's definition is read-only, in `/libexec/features/<name>/`. Its
state is the registry's, under `Machine\System\Features\<name>`, in the value
`State`:

| `State` | Means |
|---|---|
| 0 | Not installed |
| 1 | Installing (interrupted, if nothing is running) |
| 5 | Installed |
| 6 | Turning on |
| 10 | On |
| 9 | Turning off |
| 4 | Removing |

Changing a feature needs write access there. As shipped, only Administrators
have it; everyone can read it, so anyone can see what is set up.

## For a program

### `--json`

`feat list --json` answers with a JSON array, one object a feature, and
`feat info <name> --json` with one object:

| Member | Is |
|---|---|
| `name` | The feature's name, its directory under `/libexec/features/`. |
| `title`, `description` | What it says it is, from its `feature.toml`, or `null`. A description's paragraphs are separated by a blank line, with no other line breaks. |
| `state` | As `feat list` writes it. |
| `defined` | `false` for a feature whose definition is gone, known only by the state the registry still holds. |
| `phases` | The scripts it has: `install`, `enable`, `disable`, `uninstall`. |
| `may_change` | Whether you may change its state, asked of the registry (see below). |
| `metadata_problem` | Present only when its `feature.toml` couldn't be read, saying why. The feature is still listed. |

`may_change` is found by opening, for writing, the registry key a change
would write: the feature's own key, or where that isn't made yet, the key it
would be made in. Nothing is written. It says nothing of what the feature's
scripts may do, which they find out as they run.

### `--driven`

`feat --driven <command> <name>` makes a change and reports it as JSON Lines
on standard output, one event a line, for a program running `feat` on
someone's behalf (Feature Manager is one). The events are the part of
[peipkg's driven mode](~peios/peipkg/the-tools/the-driven-mode) that applies;
`feat` asks nothing, so it reads nothing, and a script's standard input is
empty.

| Event | Members | Means |
|---|---|---|
| `progress` | `phase`, `step`, `steps` | A script is starting: `phase` is `install`, `enable`, `disable` or `uninstall`, `step` of the `steps` this change will run. |
| `message` | `text` | A line a script wrote, on its standard output or error, or what `feat` says it did. |
| `done` | `summary`, `state` | The change is made, or needed nothing; `state` is the feature's now. |
| `error` | `code`, `message` | The change failed. |

Exactly one `done` or `error` ends the run. `error`'s `code` is one of
`usage`, `not-found`, `denied`, `state`, `script` (a script failed; its
output came before, as messages) and `failed`.

A program that goes away mid-change doesn't stop it: `feat` carries on and
the scripts run to their end. `list` and `info` aren't changes, so
`--driven` refuses them with a `usage` error; ask them with `--json`.

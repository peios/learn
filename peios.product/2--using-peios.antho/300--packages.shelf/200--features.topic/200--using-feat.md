---
title: Using feat
type: reference
description: The feat command — listing features, what each is, installing, turning on and off and removing them — its exit codes, and its JSON answers and driven mode for a program.
related:
  - peios/features/overview
  - peios/features/feature-manager
  - peios/writing-features/writing-a-feature
---

`feat` runs a feature's scripts and records its state. It runs them as
you: what you may change is what you could change by hand.

## Commands

| Command | Does |
|---|---|
| `feat list` | Every feature and its state, one a line: its name, a tab, and `not-installed`, `installed`, `enabled`, or an interrupted `installing`, `enabling`, `disabling` or `uninstalling`. A feature whose definition is gone is listed with a third column, `no definition`. |
| `feat info <name>` | What the feature says it is (its title and description), its state, and which scripts it has. |
| `feat install <name>` | Runs its install script. It isn't turned on. |
| `feat enable <name>` | Runs the enable script of a feature that is installed. |
| `feat disable <name>` | Runs the disable script of a feature that is on. |
| `feat add <name>` | Installs it if it isn't, then turns it on. |
| `feat remove <name>` | Turns it off if it is on, then runs its uninstall script. `feat uninstall` is the same. |

Asking for what is already so does nothing and says so:
`feat enable` on a feature that is on, `feat disable` on one that is off.
Asking again after an interruption reruns the step's script (see
[Interrupted](~peios/features/overview#interrupted)).

```
$ feat add dynamic-boot
applied 1 keys
applied 1 keys
dynamic-boot: created mkirf-watch and mkuki-watch (disabled)
feat: installed dynamic-boot
set Machine\System\Services\mkirf-watch Disabled = REG_DWORD 0   (layer: base)
set Machine\System\Services\mkuki-watch Disabled = REG_DWORD 0   (layer: base)
dynamic-boot: enabled mkirf-watch and mkuki-watch (start on next boot)
feat: enabled dynamic-boot
$ feat enable dynamic-boot
feat: dynamic-boot already enabled
```

The scripts' own output, and that of the commands they run, appears as
they run, between the lines `feat` writes.

## Exit codes

| Code | Means |
|---|---|
| 0 | Done, or nothing needed doing. |
| 1 | The command was wrong. |
| 2 | No such feature. |
| 3 | Refused: you may not change the feature's state. |
| 4 | Not possible in the feature's state: turning on one that isn't installed. |
| 5 | A script failed, or reading or writing the state failed. A failed script leaves the feature interrupted. |

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

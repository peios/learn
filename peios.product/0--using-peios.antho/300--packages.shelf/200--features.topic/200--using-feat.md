---
title: Using feat
type: how-to
description: Inspect a feature, install or enable it, turn it off or remove setup, and recover a failed lifecycle step.
related:
  - peios/features/overview
  - peios/features/feature-manager
  - peios/writing-features/writing-a-feature
---

`feat` runs a feature's scripts and records its state. It runs them as
you: what you may change is what you could change by hand.

## Inspect, change and check a feature

Start by reading the feature's own description; it tells you what setup does
and when it takes effect. For example:

```
feat list
feat info dynamic-boot
feat add dynamic-boot
feat info dynamic-boot
```

`add` installs and enables the feature. Use `install` instead if you want
setup only, or `enable` when it is already installed. For `dynamic-boot`, the
services start at the next boot; an enabled state does not mean they have
already started. Read the script output as well as the final state.

The scripts run with your rights. Permission to update the feature's state
does not guarantee permission for every action its scripts attempt.

## Turn off or remove setup

```
feat disable <name>
feat info <name>
```

This leaves the feature installed but off. To remove what it set up:

```
feat remove <name>
feat info <name>
```

`remove` turns an enabled feature off first. It does not remove the package
that supplies the scripts, so the feature remains available to set up again.
Remove setup before removing its package with peipkg.

## Recover an interrupted feature

1. Read the failed script's output and inspect `feat info <name>` or
   `feat list` to identify the interrupted phase.
2. Address the reported cause, such as missing authority or a resource the
   script needs. Updating the recorded state alone does not finish the work.
3. Run the same command again to retry the step from the start. Feature
   scripts are required to tolerate that retry.
4. Inspect the result again. If you want to back out, an interrupted enable
   can be disabled, and an interrupted install can be removed.

An interruption is recorded rather than automatically rolled back as a package
transaction. If the definition is missing, restore the supplying package first
so the feature's scripts can perform the retry or teardown. See
[Interrupted](~peios/features/overview#interrupted) and
[When its package is removed](~peios/features/overview#when-its-package-is-removed).

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

Human commands and their exit codes are above. Programs can query JSON or
run a change in driven mode; the complete schemas and error codes are in the
[feat client reference](~peios/peipkg/the-tools/feat-client-interface).

### `--json`

`feat list --json` returns an array and `feat info <name> --json` an object.
See [query members and permission checks](~peios/peipkg/the-tools/feat-client-interface#json)
for `state`, `defined`, `may_change` and the other fields. Permission to write
state says nothing about whether a script can complete its work.

### `--driven`

`feat --driven <command> <name>` emits JSON Lines for a change. It asks no
questions and gives scripts empty standard input. See
[events and terminal outcomes](~peios/peipkg/the-tools/feat-client-interface#driven).
A client going away does not stop the change; inspect its eventual state.
Use `--json` for `list` and `info`, which driven mode refuses.

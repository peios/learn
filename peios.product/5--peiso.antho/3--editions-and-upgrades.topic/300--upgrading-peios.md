---
title: Upgrading Peios
type: how-to
description: Move an installed Peios to the next release of its edition with upgrade-peios — what it runs, what it reconciles, how to stage for the next boot, and why peipkg alone will not do it.
related:
  - peios/peiso/editions-and-upgrades/editions
  - peios/peiso/editions-and-upgrades/release-toml
---

```sh
upgrade-peios
```

That is the whole procedure. It is safe to run again at any time: an interrupted upgrade is completed, and a system that is already current is left alone.

## What happens

1. **Find the edition.** `upgrade-peios` reads `ID` and `VARIANT_ID` from `/usr/lib/os-release` — the file the edition package itself wrote — and derives the edition package's name from them: `VARIANT_ID=experimental` is `dev.peios.peios-experimental`. A system whose `ID` is not `peios`, or that has no variant, is refused (exit 2).
2. **Move the edition package.** It runs `peipkg upgrade dev.peios.peios-experimental --bypass-alternate-upgrade`, passing `--yes` and `--allow-stale` through when given. The upgrade pulls the release closure with it. A peipkg failure is exit 3, and nothing further runs.
3. **Stage the release's seeds.** The new [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml) is read; each seed it names is copied from `/usr/share/regim/` into `/lcl/policy/autoapply.d/`, and the drain script is placed in `/lcl/policy/autorun.d/` if it is missing. A seed the release names that nothing ships is exit 4.
4. **Apply them.** `reg apply --dir /lcl/policy/autoapply.d --once-delete --yes` applies each seed and removes it from the queue. Services the seeds define start now. Failure is exit 5.

`upgrade-peios` never elevates. peipkg and `reg` run with the caller's token, exactly as they would if you typed the two commands yourself; KACS decides what each may do.

An installation whose `upgrade-peios` itself predates the qualified package
name is covered too. Its old concrete request for `peios-experimental` selects
the final `2026.8-10` legacy migration release. That dependency-only release
requires `dev.peios.peios-experimental`; the successor's bounded `replaces`
edge removes the legacy package in the same transaction. The migration release
therefore never enters the installed result. The successor also conflicts with
the legacy name, so trying to install the trampoline into an empty system fails
rather than leaving two edition identities behind.

## Options

| | |
|---|---|
| `--on-reboot` | Stop after staging. The seeds apply on the next boot, when peinit runs the drain script before planning its services. Use this when a seed changes something you would rather not change under a running session — the console login, say. |
| `--seeds-only` | Skip the package upgrade and only reconcile the installed release's seeds. This is the re-run: after an interrupted upgrade, or to re-apply a release's policy. |
| `--yes`, `-y` | Pass `--yes` to peipkg. |
| `--allow-stale` | Pass `--allow-stale` to peipkg: carry on with a repository's out-of-date information when refreshing it brought nothing newer. |
| `--check` | Show what upgrading would change — peipkg's `--dry-run` — and change nothing. |
| `--status` | Show the installed release, the edition package's version, the seeds waiting for the next boot, and whether you may upgrade. |
| `--root DIR` | Operate on the Peios rooted at `DIR` rather than `/`. Implies `--on-reboot`, since `reg` acts on the live registry only; peipkg is run with `--root DIR`. |

To do it on the desktop, use [Upgrade Peios](~peios/peiso/editions-and-upgrades/upgrade-peios).

## For a program

`upgrade-peios --status --json` answers with one object:

| Member | Is |
|---|---|
| `edition` | The edition package's name. |
| `name`, `version_id`, `variant` | `PRETTY_NAME`, `VERSION_ID` and `VARIANT` from os-release. |
| `version` | The edition package's installed version, or `null` where peipkg's records can't be read. |
| `queued_seeds` | The seeds waiting in `/lcl/policy/autoapply.d/` for the next boot, by name, or `null` where the queue can't be read. |
| `may_upgrade` | Whether you may upgrade: asked by opening peipkg's lock and database for writing and checking the seed queue is writable. Nothing is written. |

`upgrade-peios --driven` upgrades, or with `--check` looks, and reports it
as JSON Lines events on standard output. Its first part is
[peipkg's driven mode](~peios/peipkg/the-tools/the-driven-mode): peipkg is
run with upgrade-peios's standard input, so the program answers peipkg's
questions as it would answer peipkg's own, and every event peipkg writes is
passed on except its terminal one. Then upgrade-peios adds:

| Event | Members | Means |
|---|---|---|
| `progress` | `phase`, `step`, `steps` | `phase` is `release-stage` (the seeds are copied into the queue) or `release-apply` (they are applied). |
| `message` | `text` | What upgrade-peios is doing, or a line `reg` wrote. |
| `done` | `summary`, `edition`, `seeds_queued` | Finished; `seeds_queued` is true when the seeds were left for the next boot. |
| `cancelled` | `reason` | peipkg's plan wasn't approved; nothing was changed. |
| `error` | `code`, `message` | Failed. The code is peipkg's own for its part (`stale`, `busy`, `denied`, `unresolvable`, `untrusted`, `failed`…), or `usage`, `no-release`, `seeds` or `apply`. |

Exactly one `done`, `cancelled` or `error` ends the run. `--yes` is refused
with `--driven`. A program that goes away mid-upgrade doesn't stop it.

## From the medium

A machine with no reachable repository is upgraded from an image instead: boot it from the new medium with its disk attached and choose **Upgrade an installation** in the [installer](~peios/disks-and-filesystems/installing-to-disk). That runs the same procedure against the mounted disk — the edition with the bypass, `--seeds-only` for the seeds, then everything else the medium carries — and rewrites the boot files. The medium's repository index is fixed at manufacture, so the installer always passes peipkg `--allow-stale`, which this command does only when asked.

## Why not `peipkg upgrade`

`peipkg upgrade` upgrades every package it can and **holds the edition back**, printing the edition's message:

```text
The package "dev.peios.peios-experimental" has an alternate upgrade path.

To upgrade Peios use the `upgrade-peios` command.

Warning: Alternate upgrade paths may bypass normal peipkg protections; ensure you fully trust the authors of the package before running.
held back: dev.peios.peios-experimental 2026.8-12 -> 2026.9-1
```

`peipkg upgrade dev.peios.peios-experimental` refuses outright with the same
text. `peipkg upgrade peios-experimental` cannot name the installed qualified
package at all: named upgrades intentionally do not resolve through
`provides`. This is not peipkg being unable to move the edition; it is peipkg
declining to do only half the job. Moving a release also means reconciling its
seeds, and applying registry seeds is exactly what the package manager must
never do on a package's behalf. The refusal keeps that line where it is, and
the bypass used by `upgrade-peios` is the deliberate act that crosses it.

Once editions pin their dependencies exactly, this becomes the only way a release moves: `peipkg upgrade` cannot carry any pinned package past what the installed edition allows, so the system upgrades as a unit or not at all.

## What it does not do

- It does not upgrade packages outside the edition's closure that the edition merely floors. With `>=` floors, `peipkg upgrade` afterwards brings the rest current; with pins there is no "rest".
- It does not un-apply seeds the new release dropped. See [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml).
- It does not reboot. Whether the new kernel is running is your call, as it is after any upgrade.

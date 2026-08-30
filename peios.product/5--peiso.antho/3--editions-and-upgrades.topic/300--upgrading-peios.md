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

1. **Find the edition.** `upgrade-peios` reads `ID` and `VARIANT_ID` from `/usr/lib/os-release` — the file the edition package itself wrote — and derives the package name: `peios-` plus the variant, `peios-experimental`. A system whose `ID` is not `peios`, or that has no variant, is refused (exit 2).
2. **Upgrade the edition package.** `peipkg upgrade peios-experimental --bypass-alternate-upgrade` (with `--yes` if you passed it). The edition declares an [alternate upgrade path](~peios/peiso/editions-and-upgrades/editions), so peipkg would otherwise stop and point here; the flag is `upgrade-peios`' whole privilege. The upgrade pulls the new release's closure with it. A peipkg failure is exit 3, and nothing further runs.
3. **Stage the release's seeds.** The new [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml) is read; each seed it names is copied from `/usr/share/regim/` into `/lcl/policy/autoapply.d/`, and the drain script is placed in `/lcl/policy/autorun.d/` if it is missing. A seed the release names that nothing ships is exit 4.
4. **Apply them.** `reg apply --dir /lcl/policy/autoapply.d --once-delete --yes` applies each seed and removes it from the queue. Services the seeds define start now. Failure is exit 5.

`upgrade-peios` never elevates. peipkg and `reg` run with the caller's token, exactly as they would if you typed the two commands yourself; KACS decides what each may do.

## Options

| | |
|---|---|
| `--on-reboot` | Stop after staging. The seeds apply on the next boot, when peinit runs the drain script before planning its services. Use this when a seed changes something you would rather not change under a running session — the console login, say. |
| `--seeds-only` | Skip the package upgrade and only reconcile the installed release's seeds. This is the re-run: after an interrupted upgrade, or to re-apply a release's policy. |
| `--yes`, `-y` | Pass `--yes` to peipkg. |
| `--root DIR` | Operate on the Peios rooted at `DIR` rather than `/`. Implies `--on-reboot`, since `reg` acts on the live registry only; peipkg is run with `--root DIR`. |

## Why not `peipkg upgrade`

`peipkg upgrade` upgrades every package it can and **holds the edition back**, printing the edition's message:

```text
The package "peios-experimental" has an alternate upgrade path.

To upgrade Peios use the `upgrade-peios` command.

Warning: Alternate upgrade paths may bypass normal peipkg protections; ensure you fully trust the authors of the package before running.
held back: peios-experimental 2026.8-1 -> 2026.9-1
```

`peipkg upgrade peios-experimental` refuses outright with the same text. This is not peipkg being unable to upgrade the package; it is peipkg declining to do only half the job. Moving a release also means reconciling its seeds, and applying registry seeds is exactly what the package manager must never do on a package's behalf. The refusal keeps that line where it is, and the flag is the deliberate act that crosses it.

Once editions pin their dependencies exactly, this becomes the only way a release moves: `peipkg upgrade` cannot carry any pinned package past what the installed edition allows, so the system upgrades as a unit or not at all.

## What it does not do

- It does not upgrade packages outside the edition's closure that the edition merely floors. With `>=` floors, `peipkg upgrade` afterwards brings the rest current; with pins there is no "rest".
- It does not un-apply seeds the new release dropped. See [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml).
- It does not reboot. Whether the new kernel is running is your call, as it is after any upgrade.

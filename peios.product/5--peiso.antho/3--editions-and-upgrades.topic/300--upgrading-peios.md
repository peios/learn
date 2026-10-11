---
title: Upgrading Peios
type: how-to
description: Move an installed Peios to the next release of its edition with upgrade-peios — what it runs, what it reconciles, how to stage for the next boot, and why peipkg alone will not do it.
related:
  - peios/peiso/editions-and-upgrades/editions
  - peios/peiso/editions-and-upgrades/release-toml
---

Use `upgrade-peios` to move the edition package and reconcile the release's
registry seeds. First inspect the installed release and preview the package
plan:

```sh
upgrade-peios --status
upgrade-peios --check
```

`--check` does not apply the package plan or stage or apply registry seeds.
Planning can still refresh repository metadata for peipkg's trust-freshness
checks. It is a preview against the inputs available then, not a reserved
plan for a later invocation.

> [!WARNING]
> **Plain `upgrade-peios` can reapply policy even when no package changes.**
> In the [source versions described below](#source-and-release-scope), a
> package plan with nothing to do, or a package prompt you decline, returns
> success to the updater. It then stages the installed release's seeds and,
> on the live root without `--on-reboot`, applies the seed queue. Do not run
> the plain command just to look for updates, or rely on declining its
> package prompt to leave registry policy alone.

When you intend both the package update and seed reconciliation, run:

```sh
upgrade-peios
```

Re-running can finish seed work left by an interruption, but it also copies
the installed release's seed masters into the queue again. Review the
release's policy changes and preserve important local configuration before
reapplying them. A failed package transaction needs the
[package recovery procedure](~peios/package-management/transactions-and-recovery),
not an assumption that every interrupted step completed.

## What happens

1. **Find the edition.** `upgrade-peios` reads `ID` and `VARIANT_ID` from `/usr/lib/os-release` — the file the edition package itself wrote — and derives the edition package's name from them: `VARIANT_ID=experimental` is `dev.peios.peios-experimental`. A system whose `ID` is not `peios`, or that has no variant, is refused (exit 2).
2. **Move the edition package.** It runs `peipkg upgrade dev.peios.peios-experimental --bypass-alternate-upgrade`, passing `--yes` and `--allow-stale` through when given. The upgrade pulls the release closure with it. A peipkg failure is exit 3, and the updater stops before its seed steps. In ordinary CLI mode, peipkg exit 0 also includes a no-op or a declined prompt; those outcomes still reach the next step.
3. **Stage the installed release's seeds.** The installed [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml) is read, whether or not the package version changed; each seed it names is copied from `/usr/share/regim/` into `/lcl/policy/autoapply.d/`, and the drain script is placed in `/lcl/policy/autorun.d/` if it is missing. A seed the release names that nothing ships is exit 4.
4. **Apply the queue.** Unless staging for boot, `reg apply --dir /lcl/policy/autoapply.d --once-delete --yes` applies the queued seeds and removes successfully applied files. This command is run when the release names seeds and targets the whole directory, including other seeds already queued there. Registry policy and service definitions can change; verify their intended effects separately. Failure is exit 5, and is not a rollback of package changes or already-applied seeds.

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
| `--on-reboot` | Stop after staging. This still writes the seed queue, including after a plain-CLI no-op or declined package prompt. The seeds apply on the next boot, when peinit runs the drain script before planning its services. Use this when a seed changes something you would rather not change under a running session — the console login, say. |
| `--seeds-only` | Skip the package upgrade and only reconcile the installed release's seeds. This is the re-run: after an interrupted upgrade, or to re-apply a release's policy. |
| `--yes`, `-y` | Pass `--yes` to peipkg. |
| `--allow-stale` | Pass `--allow-stale` to peipkg: carry on with a repository's out-of-date information when refreshing it brought nothing newer. |
| `--check` | Preview peipkg's package plan with `--dry-run`; do not apply that plan or stage or apply seeds. Trust-freshness checks can still refresh repository metadata. |
| `--status` | Show the installed release, the edition package's version, the seeds waiting for the next boot, and whether you may upgrade. |
| `--root DIR` | Operate on the Peios rooted at `DIR` rather than `/`. A non-live root implies `--on-reboot`: seeds are still staged there, but `reg` is not run against the live registry. peipkg is run with `--root DIR`. |

To do it on the desktop, use [Upgrade Peios](~peios/peiso/editions-and-upgrades/upgrade-peios).
It uses driven mode: a `cancelled` result stops before seed staging and
application. This cancellation handling differs from the ordinary CLI's
exit-status check. A driven `done` result with no package operations is not
`cancelled`; without `--check`, it can still reach seed reconciliation.

## Check the outcome

Separate the package result, the seed result, and the running system:

1. Read the package result and warnings. [peipkg exit 0](~peios/package-management/keeping-a-system-current#exit-status)
   alone does not establish that an upgrade was performed or approved.
2. Run `upgrade-peios --status` again, using the same `--root DIR` for an
   alternate root. Compare the installed edition version and queued seeds.
   An unreadable queue is unknown, not empty. After `--on-reboot`, staged
   seeds are expected to remain until boot applies them.
3. If staging or application failed, read the failed step before retrying.
   Earlier seeds may already be staged or applied. `--seeds-only` stages
   the installed release's complete `autoapply` list again; it is not a
   read-only check or a reversal of the failed attempt.
4. Verify affected registry policy and the software that uses it. An empty
   queue does not by itself prove every intended service or policy is
   working. Package `undo` does not restore registry state or undo a
   feature's setup; see [recovery limits](~peios/package-management/transactions-and-recovery).

`--status` reads installed release/package metadata and the queue. It does
not identify the currently running kernel or mapped service binaries. This
updater invokes peipkg and `reg`; that path does not itself run a reboot or
boot-image regeneration command. Do not use its successful exit or status
as proof that all installed code is active or that every kernel update's
boot artifacts are ready. [Upgrading from the medium](#from-the-medium) is
a separate path with explicit boot-file regeneration.

## Check what an update has activated

Use these inspection steps after reviewing the package and seed results above.
They do not regenerate boot files, start services or restart the machine. If a
step cannot be verified, record **boot activation not yet verified** rather
than treating the update as ready to boot.

### Compare installed and running code

For a kernel update on the live system, record:

```sh
uname -r
peipkg info dev.peios.kernel
peipkg files dev.peios.kernel
```

`uname -r` identifies the running kernel release. Compare it with the intended
release in the installed kernel's payload paths, not directly with the edition
or package version: those are different identifiers. A difference before
restart is not proof that a restart will select the new kernel. For alternate
roots, select the intended package root separately; `uname` still describes
the running system.

Service status gives state, job, PID and start information, not an executing
binary's build identity. `svctl --version` is the client version. Use the
affected service's own reload/restart requirements and functional checks;
package installation or a registry-definition reload does not prove it has
adopted new code.

### Inspect Dynamic Boot's actual state

The located live regeneration mechanism is the optional **Dynamic Boot**
feature, whose scripts define `mkirf-watch` and `mkuki-watch`. Package delivery,
feature setup, enablement and running services are separate states:

```sh
feat info dynamic-boot
svctl status mkirf-watch
svctl status mkuki-watch
svctl definition show mkirf-watch
svctl definition show mkuki-watch
```

The reviewed feature initially creates disabled services. Enabling it after
boot clears that flag but does not retroactively start them; disabling it does
not stop an already-running watcher. Image setup before boot-time service
enumeration can differ. Check the actual services rather than inferring their
state from the feature record. This section supplies no automatic start or
restart sequence.

In the packaged definitions, `mkirf-watch` writes
`/system/boot/initramfs.cpio.zst`, and `mkuki-watch` writes
`/boot/efi/EFI/BOOT/BOOTX64.EFI`. Verify the definitions on your machine. The
UKI launcher chooses its command-line input at startup: a nonempty
`/lcl/etc/boot/cmdline`, otherwise `/usr/share/live-boot/cmdline`. Creating the
preferred file later does not prove an existing watcher switched to it.

### Verify the destination and rebuild evidence

Before relying on watcher output, use [storage inspection](~peios/mount-policies/managing-mounts#inspect-live-mounts-and-policy)
to identify the intended EFI System Partition and the filesystem at the output
path. Plain `mount` lists mounts visible in the caller's namespace; that is not
proof of firmware selection or another namespace's view.

> [!WARNING]
> `mkuki` can create missing output directories without checking that they are
> on the intended ESP. A **wrote** message can therefore describe an ordinary
> directory, not the boot partition. The reviewed feature scripts do not supply
> a complete ESP-mount arrangement. If the mapping is absent or uncertain,
> stop the boot-readiness claim; do not choose a device or create a mount recipe
> by guesswork.

In **Services Manager**, inspect **Logs…** for each watcher over the update's
job/time interval. Both can report `rebuild failed` and remain running; an
Active/Alive state or **watching** message is not build success. `mkuki` also
rejects zero or multiple regular `vmlinuz-*` candidates rather than selecting
the newest one.

Look for successful cpio replacement and a subsequent successful UKI rebuild
using the final settled inputs, retaining all rebuild/watch errors. A **wrote**
message follows output replacement, but the watchers run independently of the
package transaction: it is not an all-input generation or bootability
attestation. Intermediate builds can observe different update stages. Missing
logs or timestamps alone cannot establish success; [log visibility and delivery
limits](~peios/services-and-jobs/output-and-logging) still apply.

### Check after a separately planned restart

Only follow the machine's supported restart procedure once its prerequisites
and recovery access are established. After it actually boots, run `uname -r`
again and compare the intended release. Check queued-seed state, affected
service jobs/status and their functional behavior separately. An accepted
restart request, installed edition name or old successful build message does
not replace these observations.

The [installer-medium upgrade](#from-the-medium) is a separate path that mounts
its selected ESP and explicitly rebuilds boot files. It is not evidence that
the live watcher destination is configured, nor a harmless generic repair.

### Activation evidence and scope

This checklist follows pinned static source, not a deployed-system test:

- [Dynamic Boot setup](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.feat-dynamic-boot/src/install.sh#L13-L42),
  [enable](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.feat-dynamic-boot/src/enable.sh#L2-L12),
  [disable](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.feat-dynamic-boot/src/disable.sh#L2-L12),
  and [launcher paths](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.feat-dynamic-boot/src/watch-uki.sh#L18-L34).
- [mkirf failure handling](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/mkirf/src/watch.rs#L44-L85)
  and [mkuki watch/build behavior](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/mkuki/src/mkuki.rs#L263-L440).
- [Kernel payload naming](https://github.com/peios/pkm/blob/8e0e22de3a59cad506bbbf8873de456e16ad272d/packages.pekit/kernel.package.pekit.toml#L7-L32)
  and [running-kernel readback](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/uname/src/uname.rs#L61-L87).
- [Installer boot-file generation](https://github.com/peios/installer/blob/0b687372ad41132668824216da51558bbfe53c01/installerd/src/real.rs#L818-L890).

Check applicability to your image. These sources establish separate stages,
not a complete live ESP setup, combined artifact verifier or successful boot.

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
| `cancelled` | `reason` | peipkg's plan wasn't approved; the updater stops before staging or applying seeds. |
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
- It does not reboot or verify runtime activation. Check the running system separately from the installed package version.

## Source and release scope

The CLI/driven distinction above follows
[peiosutils `3344d469`'s upgrade path](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/upgrade-peios/src/upgrade_peios.rs#L243-L344),
its [seed-copying step](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/upgrade-peios/src/upgrade_peios.rs#L515-L566),
and [peipkg `8b588ae8`'s plan/approval return path](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L373-L444).
Peipkg performs [trust-freshness checks before its dry-run boundary](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L192-L223).
The [status implementation](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/upgrade-peios/src/status.rs#L19-L108)
establishes the limits of the inspection command. These are source-backed
behaviours, not a live cancellation/upgrade test or proof that a particular
released image includes these revisions. Check the tool versions supplied
by the image you operate.

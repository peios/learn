---
title: Keeping a system current
type: how-to
description: refresh learns what is available; upgrade moves to it; downgrade and undo walk a bad change back. The routine update cycle and the recovery commands.
related:
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/transactions-and-recovery
  - peios/package-management/dependency-resolution
  - peios/package-management/named-roots
---

For routine maintenance, refresh, review the upgrade plan, apply it, then
check the outcome. First choose the intended [root](~peios/package-management/named-roots)
and preserve important local changes. `upgrade` can also update nested roots,
so review the whole plan and check every participating root afterwards.

```
peipkg refresh
peipkg upgrade --dry-run
peipkg upgrade
peipkg history
peipkg verify
```

Read refresh failures before proceeding: a dry run and the final invocation
can use different inputs if metadata or installed packages changed in between.
After the change, review verification differences and configuration-file
warnings, and check the affected software separately. A file check does not
establish that a service or feature is working. For kernel and service updates,
follow [Check what an update has activated](~peios/peiso/editions-and-upgrades/upgrading-peios#check-what-an-update-has-activated)
to distinguish installed payloads, boot artifacts and running code.

| Your situation | Command |
|---|---|
| Apply available updates | `upgrade`, after `refresh` and plan review |
| Reverse the most recent committed transaction | `undo`, after checking `history` and its dry run |
| Restore one package to a particular older version | `downgrade <package> <version>` |
| An operation was interrupted and is pending | [`recover`](~peios/package-management/transactions-and-recovery), then verify |

Version reversal changes package payloads. It does not reverse registry
state, runtime or user data, or setup performed by feature scripts.

For the Peios edition itself, use [Upgrading Peios](~peios/peiso/editions-and-upgrades/upgrading-peios).
Its plain CLI also reconciles release seeds after a no-op or declined
package request; `peipkg`'s exit 0 is not a cancellation signal to that
wrapper. Use `upgrade-peios --check` to preview without staging or applying
seeds.

## Refreshing repository metadata

```
peipkg refresh [repository]...
```

peipkg plans against a local, verified copy of each repository's metadata. That copy does not update itself. `peipkg refresh` is what updates it: for every configured repository — or just the ones you name — peipkg fetches the current signed descriptor and index, verifies them, and replaces the cached copy.

```
$ peipkg refresh
refreshed "official"
refreshed "internal"
```

Refresh has two properties worth knowing:

- **Repositories are independent.** If one repository is unreachable or fails verification, peipkg reports it and carries on with the rest. One bad repository never blocks a refresh of the others.
- **A failed refresh changes nothing.** If a repository cannot be refreshed, peipkg keeps the metadata it already had. It never falls back to unverified or stale-but-unchecked content. The worst a failed refresh does is leave you on yesterday's view.

What "verified" means here — signing keys, freshness floors, the handling of an unsigned repository — is the subject of [Repositories and trust](~peios/package-management/repositories-and-trust).

Run `refresh` before an upgrade. An upgrade plans against cached metadata, so without a recent refresh it cannot consider newer releases that the cache does not contain. The selected version still depends on the request, source preferences and constraints.

Skip it for long enough and peipkg stops waiting for you: an install, upgrade, or downgrade against a repository whose trust state has passed its **maximum trusted age** (30 days by default) refreshes that repository itself, and refuses to proceed against one that stays stale — unreachable, or frozen on an unchanging index — unless you pass `--allow-stale`. The bound and its configuration are covered in [Repositories and trust](~peios/package-management/repositories-and-trust).

## Upgrading

```
peipkg upgrade [package]...
```

With no arguments, `upgrade` considers every installed package in the
current root and its reachable named roots for a newer version that satisfies
resolution. With package names, it considers those packages in each reachable
root where they are installed, including any new dependencies they need.
`--no-recurse` confines resolution and execution to the current root.

```
$ peipkg refresh && peipkg upgrade
the following changes will be made:
  upgrade    zlib 1.3.1 -> 1.3.2
  upgrade    nginx 1.27.4 -> 1.27.5
proceed? [y/N]
```

`upgrade` uses the same plan-and-confirm flow as `install` — peipkg shows the full set of changes and waits for approval — and the same options:

| Option | Effect |
|---|---|
| `--dry-run` | Print the plan and stop. A good way to preview what an upgrade would move. |
| `--yes`, `-y` | Skip the `proceed?` prompt. |
| `--no-recurse` | Confine the upgrade to the current root only — disable the cascade into nested named roots. |
| `--allow-stale` | Proceed although a repository's trust state exceeds its maximum trusted age. Warned and audited. |

By default, `upgrade` resolves **one combined plan** over the current root
and its reachable named roots. One approval covers that plan. If it changes
more than one root, peipkg coordinates the participants as a cross-root
transaction, not independent per-root upgrades. Preparation failure attempts
rollback; a later commit failure can leave some roots committed and others
pending. Read [the named-root transaction boundaries](~peios/package-management/named-roots#cascading-upgrade)
and [cross-root recovery](~peios/package-management/transactions-and-recovery#across-more-than-one-root)
before treating a failed operation as unchanged. This describes
[peipkg `8b588ae8`'s upgrade entry](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L188-L223)
and [single approval/executor selection](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L338-L383);
check the revision supplied by your image.

If the plan contains no updates, peipkg says so and exits. That is a result against the available metadata and constraints, not proof that every upstream release is installed.

## Downgrading

```
peipkg downgrade <package> <version>
```

`downgrade` moves one package to a specific older version. You name the package and the exact version you want:

```
$ peipkg downgrade nginx 1.27.4
```

Older versions are not in a repository's active index — that index lists current versions only. They live in its **archive index**, which peipkg fetches on demand when you ask for a version that is not current. The package must still exist in some configured repository's archive for the downgrade to be possible.

A downgrade is treated as a deliberate move. Going backward — onto a version that may have known issues a newer one fixed — is one of the actions peipkg flags for **explicit authorisation**: beyond the routine `proceed?` prompt, peipkg asks you to authorise the specific downgrade, and `--yes` does not stand in for that answer. See [Elevated authorisation](~peios/package-management/dependency-resolution) for the full set of actions that work this way.

`downgrade` accepts `--dry-run`, `--yes`, `-y`, and `--allow-stale` with the same meaning as elsewhere.

## Undoing the last change

```
peipkg undo
```

Before applying `undo`, identify the most recent committed transaction:

```
peipkg history
peipkg undo --dry-run
```

`undo` reverses the most recent committed transaction. If that transaction installed a package, `undo` removes it; if it upgraded, downgraded, or removed packages, `undo` restores each one to the version it had before.

```
$ peipkg undo
undoing transaction 47 (upgrade nginx, zlib)
the following changes will be made:
  downgrade  nginx 1.27.5 -> 1.27.4
  downgrade  zlib 1.3.2 -> 1.3.1
proceed? [y/N]
```

Check that the old packages are available before relying on undo. The
[technical reference](~peios/peipkg/upgrade-and-removal/downgrade-and-undo#undo)
describes archive-based resolution requiring a reachable repository or usable
cache; it does not promise retained transaction backups. Even where undo is
exempt from freshness gating, that does not guarantee it can fetch an old
version offline.

Be precise about what `undo` is. It is not a rollback of committed state — the previous transaction happened and stays in the history. `undo` computes the inverse of that transaction and applies it as a new transaction of its own. The history grows; it does not rewind. That new transaction can itself be undone, and so on.

Because restoring an older version is a backward move, `undo` carries the same explicit-authorisation requirement as `downgrade` for any package it walks back. It accepts `--dry-run` and `--yes`, `-y`.

To undo something other than the most recent transaction, or to see the history `undo` works against, use [`peipkg history`](~peios/package-management/transactions-and-recovery) — and revert a specific package directly with `downgrade`.

## The routine cycle

For day-to-day maintenance the loop is:

```
$ peipkg refresh        # learn what is available
$ peipkg upgrade --dry-run   # preview the move
$ peipkg upgrade        # apply it
```

`downgrade` and `undo` are the recovery commands — use them when an upgrade has brought in a change you want to remove. They apply a new package transaction. Read the [recovery limits](~peios/package-management/transactions-and-recovery) before relying on another reversal, and verify after a failed or interrupted attempt.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — including a dry run, a plan with nothing to do, and a declined prompt or authorisation (nothing failed). |
| `1` | The operation failed — a repository could not be refreshed, a repository's trust state exceeded its maximum age and a forced refresh could not clear it, resolution or a download or verification failed, cross-root preparation, commit or recovery failed, there is no committed transaction to undo, or a command's arguments were wrong (`downgrade` without a package and version, an unparsable version, a malformed option). |
| `2` | A usage error before any command ran — no command, an unknown command, or a malformed global option (including a `--root` reference that does not resolve). |

---
title: Keeping a system current
type: reference
description: refresh updates the metadata peipkg plans against; upgrade moves packages forward to their newest versions; downgrade and undo move them back. Together they are the routine update cycle and the way to walk a bad change off the system.
related:
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/transactions-and-recovery
  - peios/package-management/dependency-resolution
---

Keeping a Peios system current is two commands in sequence — `refresh` to learn what is available, then `upgrade` to move to it. The other two commands here, `downgrade` and `undo`, go the other way: they walk a change back when an upgrade turns out badly.

## Refreshing repository metadata

```
peipkg refresh [repository]...
```

peipkg plans against a **local, verified copy** of each repository's metadata. That copy does not update itself. `peipkg refresh` is what updates it: for every configured repository — or just the ones you name — peipkg fetches the current signed descriptor and index, verifies them, and replaces the cached copy.

```
$ peipkg refresh
refreshed "official"
refreshed "internal"
```

Refresh has two properties worth knowing:

- **Repositories are independent.** If one repository is unreachable or fails verification, peipkg reports it and carries on with the rest. One bad repository never blocks a refresh of the others.
- **A failed refresh changes nothing.** If a repository cannot be refreshed, peipkg keeps the metadata it already had. It never falls back to unverified or stale-but-unchecked content. The worst a failed refresh does is leave you on yesterday's view.

What "verified" means here — signing keys, freshness floors, the handling of an unsigned repository — is the subject of [Repositories and trust](~peios/package-management/repositories-and-trust).

Run `refresh` before an upgrade. An upgrade plans against whatever metadata is cached, so an upgrade without a recent refresh simply moves you to the newest version peipkg *last heard about*.

## Upgrading

```
peipkg upgrade [package]...
```

With no arguments, `upgrade` considers **every installed package** and moves each one that has a newer available version forward to it. With one or more package names, it upgrades only those — and still pulls in any new dependencies they need.

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

If there is nothing to do — every package already at its newest version — peipkg says so and exits.

## Downgrading

```
peipkg downgrade <package> <version>
```

`downgrade` moves one package to a **specific older version**. You name the package and the exact version you want:

```
$ peipkg downgrade nginx 1.27.4
```

Older versions are not in a repository's *active* index — that index lists current versions only. They live in its **archive index**, which peipkg fetches on demand when you ask for a version that is not current. The package must still exist in some configured repository's archive for the downgrade to be possible.

A downgrade is treated as a deliberate move. Going *backward* — onto a version that may have known issues a newer one fixed — is one of the actions peipkg flags for **explicit authorisation**: beyond the routine `proceed?` prompt, peipkg asks you to authorise the specific downgrade, and `--yes` does not stand in for that answer. See [Elevated authorisation](~peios/package-management/dependency-resolution) for the full set of actions that work this way.

`downgrade` accepts `--dry-run` and `--yes`, `-y` with the same meaning as elsewhere.

## Undoing the last change

```
peipkg undo
```

`undo` reverses the **most recent committed transaction**. If that transaction installed a package, `undo` removes it; if it upgraded, downgraded, or removed packages, `undo` restores each one to the version it had before.

```
$ peipkg undo
undoing transaction 47 (upgrade nginx, zlib)
the following changes will be made:
  downgrade  nginx 1.27.5 -> 1.27.4
  downgrade  zlib 1.3.2 -> 1.3.1
proceed? [y/N]
```

It is worth being precise about what `undo` is. It is **not** a rollback of committed state — the previous transaction really did happen and stays in the history. `undo` computes the *inverse* of that transaction and applies it as a brand-new transaction of its own. The history grows; it does not rewind. That new transaction can itself be undone, and so on.

Because restoring an older version is a backward move, `undo` carries the same explicit-authorisation requirement as `downgrade` for any package it walks back. It accepts `--dry-run` and `--yes`, `-y`.

To undo something *other* than the most recent transaction, or to see the history `undo` works against, use [`peipkg history`](~peios/package-management/transactions-and-recovery) — and revert a specific package directly with `downgrade`.

## The routine cycle

For day-to-day maintenance the loop is:

```
$ peipkg refresh        # learn what is available
$ peipkg upgrade --dry-run   # preview the move
$ peipkg upgrade        # apply it
```

`downgrade` and `undo` are the recovery moves — reach for them when a refreshed-and-upgraded system has picked up a change you want gone. Every one of these commands is a [transaction](~peios/package-management/transactions-and-recovery), so every one of them is atomic and itself reversible.

---
title: Editions
type: concept
description: "A Peios release is an edition package: its version is the OS version, its closure is the base system, it owns os-release and release.toml, and it declares that only upgrade-peios may move it."
related:
  - peios/peiso/editions-and-upgrades/release-toml
  - peios/peiso/editions-and-upgrades/upgrading-peios
  - peios/peiso/building-images/overview
---

Peios has no channels and no release cadence. It is a rolling release with a full archive: every version of every package ever published stays installable. What it has instead of a channel is an **edition** — a package that says what a Peios is.

## The edition package

`peios-experimental` is the edition today. It is an ordinary peipkg package with an unusual job:

- **Its version is the OS version.** `peios-experimental 2026.8-1` is Peios 2026.8. The package writes `/usr/lib/os-release` (`VERSION_ID="2026.8"`, `VARIANT_ID=experimental`, `PRETTY_NAME="Peios 2026.8 Experimental"`) and the `/usr/etc/os-release` compatibility symlink, so a system's identity and its release are one fact, tracked in the package database.
- **Its dependencies are the base system.** Kernel, modules and firmware; the initramfs — `prelude`, its hooks, the module subset and its own base tree, each placed `IN initramfs` explicitly; the service manager, registry, identity and networking daemons; the installer. Installing the package into an empty root yields a bootable Peios.
- **It provides `peios-release`.** Depend on that virtual name to mean "some Peios"; depend on the edition to mean that edition.
- **It ships [`release.toml`](~peios/peiso/editions-and-upgrades/release-toml)**: what the release asks of a system beyond its packages, as data.
- **It declares an alternate upgrade path.** peipkg refuses to install or upgrade it by name, holds it back from an upgrade of everything, and prints the message it carries: *To upgrade Peios use the `upgrade-peios` command.* The reasons are below.

"Experimental" is a name, not a channel. It marks that Peios is not yet production-ready and says nothing about cadence. When enough exists for the split to make sense it is replaced by `peios-pro`, `peios-minimal`, `peios-desktop` and so on — each its own package, each providing `peios-release`, each shipping its own `os-release`.

## What the edition deliberately does not contain

Three things a live medium needs are absent from the edition, because they are properties of the medium:

- **`live-boot`** and **`disk-boot`.** Which boot packages a system carries depends on what it boots from. The installer swaps one for the other on the target; an edition that named either would be installable on only one kind of medium.
- **`peios-dwe`.** The Developer Workstation Environment makes a machine ownable. It is added by peiso for a development medium and could never be a thing that arrives by installing a package.
- **Anything the installer is not.** `peios-install` *is* in the edition: an installed system can install another.

## Pinning

Experimental's dependencies are `>=` floors — a floor lets a package move without republishing the edition on every change, which is right for a pre-alpha. A production edition pins exact versions, and then something useful follows: `peipkg upgrade` cannot move a pinned dependency past what the edition allows, so a real release upgrades as a unit, through `upgrade-peios`, never piecemeal.

## Why the package manager will not move it

Installing a package on Peios cannot change system policy. A package delivers files; which services run and which policies apply is decided by registry seeds that a package can only *offer*. That is the deliberate weakness that lets packages be installed freely.

Moving from one release to the next is more than a package upgrade: the new release's seeds have to be reconciled, and that is precisely the thing peipkg must not do. So the edition declares, in its manifest, `alternate_upgrade = { message = "To upgrade Peios use the `upgrade-peios` command." }` (PSPU §5.18). The declaration grants nothing — a package cannot name a command for the consumer to run, let alone run one. Its whole effect is that peipkg stops and shows the message, with a warning that whatever the message names sits outside the package manager's protections. The person runs [`upgrade-peios`](~peios/peiso/editions-and-upgrades/upgrading-peios), which drives peipkg with `--bypass-alternate-upgrade` and then does the reconciling itself.

## Where an edition lives

The recipe is `pkgs/peios-experimental/` in the Peios tree: a `pekit.toml` whose build writes `os-release` and `release.toml`, and a `package.pekit.toml` with the dependency table. Changing what Peios contains is a change there, followed by a republish. peiso and its spec do not change.

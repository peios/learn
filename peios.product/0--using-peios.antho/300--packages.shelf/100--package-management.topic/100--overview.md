---
title: Package management
type: how-to
description: Choose the package or feature task, check your authority and source, apply a reviewed change, and verify or recover it.
related:
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/transactions-and-recovery
  - peios/package-management/claims
  - peios/package-management/named-roots
  - peios/package-management/composing-a-root
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
---

Use **peipkg** to install, update, remove and inspect package files. Use
**feat** when you need to set up or turn on a feature supplied by a package.
Both run as you, and neither gives you additional authority.

## Where to start

| What you need | Start here |
|---|---|
| Find, install or remove software | [Installing and removing packages](~peios/package-management/installing-and-removing) |
| Apply updates or reverse a committed change | [Keeping a system current](~peios/package-management/keeping-a-system-current) |
| Add or repair a package source | [Repositories and trust](~peios/package-management/repositories-and-trust) |
| Understand an unexpected plan or a separate approval | [Dependency resolution](~peios/package-management/dependency-resolution) |
| Check files or identify their owner | [Inspecting and verifying](~peios/package-management/inspecting-and-verifying) |
| Recover after a failed or interrupted operation | [Transactions and recovery](~peios/package-management/transactions-and-recovery) |
| Choose which package supplies a shared name | [Claims](~peios/package-management/claims) |
| Work on an offline installation or initramfs | [Named roots](~peios/package-management/named-roots) |
| Turn a feature on or remove its setup | [Using feat](~peios/features/using-feat) |
| Assemble a new image's package tree | [Composing a root](~peios/package-management/composing-a-root) |

For desktop work, open [Package Manager](~peios/package-management/package-manager)
from the launcher by typing `package`, or
[Feature Manager](~peios/features/feature-manager) by typing `feature`.

## What a package is

A `.peipkg` file carries a package's identity, version, architecture,
dependencies and payload. peipkg records the installed package and the files
it owns, so it can inspect, replace, remove and verify those files.

Installing a package makes its files available. A [feature](~peios/features/overview)
performs additional setup through scripts you explicitly run, such as
registering or enabling a service. Package installation does not run those
scripts. Remove a feature's setup before removing the package that supplies it.

A package can also provide a [claim](~peios/package-management/claims), a
shared filesystem name with one holder. That chooses a provider; it is not
the same operation as enabling a feature. Archive and manifest internals
belong in the [technical reference](~peios/peipkg/introduction/what-this-manual-covers).

## Where packages come from

Repositories supply package files and signed metadata. `peipkg refresh`
updates the cached metadata used to plan installs and updates. Before adding
a repository, obtain its signing-key fingerprint through a trusted channel;
[configuration alone is not trust](~peios/package-management/repositories-and-trust#adding-a-repository-your-system-already-carries).

A [local `.peipkg` file](~peios/package-management/installing-and-removing#installing-from-a-local-file)
can also be installed. Its format and payload hashes are checked, but there
is no repository trust chain authenticating it. You are vouching for that file.

## peipkg has no authority of its own

peipkg is an ordinary program running under your token. It has no privileged
daemon, setuid identity, service account or broker. The system checks your
rights against the [security descriptors](~peios/security-descriptors/overview)
on the paths it changes and the state it reads or writes.

As shipped, package administration is for Administrators. Granting write
access to package destinations is broader than permission to install one
approved package: peipkg cannot provide that narrower permission for you.
A package's requested security descriptor cannot give its installer authority
the installer did not already have. See the
[privilege model](~peios/peipkg/security/the-privilege-model) for the boundary.

## Every change is a transaction

peipkg shows a plan before applying a change. Review every dependency,
removal, source, version and target root, then read the final outcome and
warnings. `--yes` skips only the routine approval; it does not approve the
separate questions for elevated actions or modified configuration files.

Use `undo` or `downgrade` for a completed change you want to reverse, and
`recover` for a pending interrupted transaction. They do not restore feature
setup, registry state or user data. The technical reference documents
rollback failures and recovery limits, so do not treat an error or a
`rolled-back` history entry as proof that every file was restored.
[Verify after recovery](~peios/package-management/transactions-and-recovery).

## Every operation is audited

Package operations and deliberate authorisations produce semantic events in
the [audit stream](~peios/auditing/overview). There are documented exceptions:
automatic recovery emits no peipkg event, and event emission can fail without
stopping a package change. The [audit reference](~peios/peipkg/security/audit)
describes these limits. The kernel's audit of the actual file operations is
the security record; peipkg's events are a useful summary.

## The command surface

Every command is invoked as `peipkg <command> [arguments]`.

| Command | Does |
|---|---|
| `install` | Install packages, with dependencies, from a repository or a local `.peipkg` file. |
| `remove` (alias `uninstall`) | Remove installed packages. |
| `upgrade` | Update installed packages under the available sources and constraints. |
| `downgrade` | Move one package to a specific older version. |
| `undo` | Reverse the most recent committed transaction as a new change. |
| `claim` | Show or change which package holds a claim — a shared name that exactly one package may own. |
| `refresh` | Update the cached metadata of the configured repositories. |
| `repo` | Configure repositories — `add`, `list`, `remove`. |
| `root` | Manage named roots — `add`, `list`, `remove`, `show`. |
| `list` | List the installed packages. |
| `info` | Show one installed package's details. |
| `files` | List the files a package owns. |
| `owns` | Report which package owns a given path. |
| `search` | Search the configured repositories for a package. |
| `verify` | Check installed files against what was recorded at install. |
| `history` | Show the transaction log. |
| `recover` | Recover pending work; cross-root recovery may roll forward. |
| `clean` | Delete unused metadata-cache data; see the documented cache-scope limits. |

One global option sits before the command: `--root TARGET` makes peipkg operate on a Peios installation other than the running system at `/`. `TARGET` can be a literal path — a Peios installation mounted at `DIR`, the form used by image builders and offline maintenance — or the name of a [named root](~peios/package-management/named-roots). Named roots are more than a convenience: they are how peipkg keeps components such as the initramfs current. See [Named roots](~peios/package-management/named-roots) for the detail.

## The producer side

Building and signing packages is [pekit](~pekit/getting-started/what-is-pekit)'s
job; publishing repositories is [`peipkg-repo`](~peios/peipkg/the-tools/peipkg-repo)'s.
See the [Producing packages](~peios/peipkg/producing-packages/the-recipe-family)
reference for that work. `peipkg-compose` is a separate consumer-side binary
for assembling a fresh root, not a `peipkg` subcommand or a live-system updater.

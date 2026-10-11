---
title: Installing and removing packages
type: how-to
description: Find a package, review and apply its plan, verify the result, and remove it without leaving feature setup behind.
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/dependency-resolution
  - peios/package-management/transactions-and-recovery
  - peios/package-management/claims
  - peios/package-management/named-roots
---

Use `peipkg` for package files and [feat](~peios/features/using-feat) for the
setup a package's features perform. Installing a feature's package makes its
scripts available; it does not turn the feature on. On the desktop, use
[Package Manager](~peios/package-management/package-manager).

## Before changing software

- Check that you are working on the intended [root](~peios/package-management/named-roots).
  The default is `/`; a package's `default_root` can redirect an install when
  you have not specified `--root`.
- You need access to peipkg's records and authority to write the affected
  paths. peipkg runs as you and grants no additional rights.
- Use a repository whose signing-key anchor you have verified through a
  trusted channel. See [Repositories and trust](~peios/package-management/repositories-and-trust).
- Keep an independent copy of important local changes before replacing or
  removing files. Transaction recovery and version undo have
  [documented limits](~peios/package-management/transactions-and-recovery).

## Install and check a package

For example, to install GNU Grep from a configured, trusted repository:

```
peipkg refresh
peipkg search grep
peipkg install org.gnu.grep --dry-run
peipkg install org.gnu.grep
peipkg info org.gnu.grep
peipkg verify org.gnu.grep
```

Review the source, versions, dependencies, removals, claims and target roots
in the plan before approving. A dry run does not reserve its inputs: review
the plan again when applying, especially after refreshing metadata or
another package change. `info` shows the installed version and origin;
`verify` checks files, not whether the application is running or configured.

If the operation fails or is interrupted, use the
[recovery procedure](~peios/package-management/transactions-and-recovery#recovering-an-interrupted-transaction)
before treating the system as restored.

## Installing packages

```
peipkg install <package|file.peipkg>...
```

Each argument is either the **name** of a package to fetch from a configured repository, or the **path** of a local `.peipkg` file (recognised by its `.peipkg` suffix). You can mix the two in one command.

### Canonical package names

Use the complete canonical name returned by `peipkg search`. Current catalogue
commands do not resolve a short final component such as `grep` to
`org.gnu.grep`. Virtual capabilities remain unqualified and are a separate
[dependency mechanism](~peios/package-management/dependency-resolution).

Canonical names use reverse-DNS namespaces, for example `org.gnu.bash`,
`com.amd.amd-ucode` and `org.peios.peinit`. Third-party software retains its
upstream namespace; Peios-owned software uses `org.peios`. A name identifies
the software, not who signed or endorsed the package. Check its repository
origin separately.

The [catalogue package-family reference](~peios/peipkg/catalogue-package-families)
retains the full name list, split-library and development packages, included
commands, unsupported components, and build/trust qualifications.

Installing a package rarely means installing just that package. peipkg works out everything the request implies — the dependencies the package needs, and the dependencies of those in turn — and presents the whole set. How that set is computed is the subject of [Dependency resolution](~peios/package-management/dependency-resolution); this page is about the flow around it.

### The plan-and-confirm flow

`install`, `remove`, and the commands on [Keeping a system current](~peios/package-management/keeping-a-system-current) all work the same way. peipkg first produces a **plan** — the ordered list of changes that satisfy your request — and prints it:

```
$ peipkg install nginx
the following changes will be made:
  install    pcre2 10.44
  install    zlib 1.3.1
  install    nginx 1.27.4
proceed? [y/N]
```

For repository packages, presenting this plan does not download or install their payloads. peipkg waits for an answer. Anything other than `y` or `yes` — including pressing Enter, or end-of-input — is a refusal, and the package plan is not applied. This is the package command's outcome; a wrapper such as [plain `upgrade-peios`](~peios/peiso/editions-and-upgrades/upgrading-peios) can still continue with its own registry-seed work.

Answer `y` and peipkg carries the plan out as a single [transaction](~peios/package-management/transactions-and-recovery): it downloads and verifies every package, then applies the change. Read the outcome and any warnings; after an interruption, follow the recovery procedure.

| Option | Effect |
|---|---|
| `--dry-run` | Produce and print the plan, then stop before its approval questions and package application. Planning can still refresh repository metadata for trust-freshness checks. |
| `--yes`, `-y` | Skip the `proceed?` prompt and apply the plan. |
| `--no-claim` | Install a provider without taking any claim it offers. |
| `--allow-stale` | Proceed although a repository's trust state exceeds its maximum trusted age. See [Repositories and trust](~peios/package-management/repositories-and-trust). |
| `--claim <names>` | Comma-separated claims to force-claim, overriding the current holder(s). |
| `--claim-all` | Force-claim every claim the installed packages provide, overriding incumbents. |
| `--dangerously-bypass-path-restrictions` | Permit packages that declare `special_system_package` to install outside the payload layout rules. Exempts nothing that has not declared itself special. The technical sources disagree on whether `/lcl/policy` remains protected under the bypass; do not rely on that exclusion (see the warning below). Needed only for the handful of packages whose job is to lay down the filesystem structure those rules protect. |

`--dry-run` previews the package plan without applying it. In
[peipkg `8b588ae8`](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L23-L86),
trust-freshness checks precede planning, and the
[dry-run return](https://github.com/peios/peipkg/blob/8b588ae81ebe08a567843767f3c21d9c24675e49/internal/cli/lifecycle.go#L373-L444)
is before plan authorisation and execution. Do not treat it as a guarantee
that cached metadata or all filesystem state is untouched. Check the source
scope against the version in your image.

`--yes` is for scripts and unattended runs — but note that it skips only the routine prompt. A plan that contains an action needing deliberate authorisation will still stop and ask; `--yes` does not override that. See [Elevated authorisation](~peios/package-management/dependency-resolution) for which actions those are and why.

> [!WARNING]
> The [installation validation reference](~peios/peipkg/installation/validation#destinations-are-checked-here)
> says the special-package bypass skips the destination check entirely,
> including `/lcl/policy`; earlier operator guidance said that path was
> excluded. This documentation does not establish a narrower boundary.
> Only grant the bypass after reviewing the package's destinations and the
> authority of the account running it.

`--claim-all` cannot be combined with `--claim` or `--no-claim`. Claims — shared names exactly one package may hold — are covered in [Claims](~peios/package-management/claims).

An install can also target a root other than the current one — either explicitly with `--root`, or because a package declares its own default root. See [Named roots](~peios/package-management/named-roots) for how roots are named and nested.

### Installing from a local file

When an argument is a path ending in `.peipkg`, peipkg installs that file directly:

```
$ peipkg install ./nginx-1.27.4.peipkg
```

This is a **raw install**, and it differs from a repository install in one specific way: it skips the repository **trust layer**. There is no signed index to check the file against, no signing key to verify it under, and none of the freshness or rollback protection a repository provides. You are vouching for the file yourself.

Everything else still happens. The package format is fully verified: the archive structure, the manifest, the integrity manifest, and the hash of every payload file are all checked before anything is staged. A corrupt or truncated `.peipkg` is rejected in the same way as one from a repository. The file's dependencies still resolve normally against your configured repositories — a locally-installed package can pull in repository packages to satisfy what it needs.

A package supplied as an explicit local file takes precedence over any repository's version of the same package, so `install ./foo.peipkg` installs that file even if a repository offers `foo` too. In the plan, a local-file operation is marked so the choice is visible:

```
  install    nginx 1.27.4  (local file)
```

There is currently no policy gate that refuses raw installs as a class. Format and hash checks establish integrity, not the file's publisher or trustworthiness.

## Removing packages

```
peipkg remove <package>...
peipkg uninstall <package>...
```

`remove` and `uninstall` are the same command. Each argument names an installed package; peipkg plans the removal — the files to take off disk — and runs the plan-and-confirm flow described above.

Before removing a package that supplies a feature, inspect and remove that
feature with `feat` first. Removing the package does not undo the feature's
setup and takes away the scripts needed to undo it. If that already happened,
[restore the feature definition](~peios/features/overview#when-its-package-is-removed)
before removing the feature.

Inspect the package and preview the removal:

```
peipkg info <package>
peipkg files <package>
peipkg remove <package> --dry-run
peipkg remove <package>
peipkg list
peipkg history
```

A removal releases the package's files and claims. Shared or non-empty
directories remain; empty directories owned by no remaining package can be
removed. If the package held a claim, no alternative is promoted
[automatically](~peios/package-management/claims#what-happens-on-uninstall).

### Keep or remove local changes

For a modified configuration file under `/usr/etc/` or the legacy `/etc/`,
peipkg asks whether to remove it, keep it, or abort:

- **Remove:** the prior content is kept at a sibling backup path.
- **Keep:** the file stays but becomes unowned.
- **Abort:** the removal stops. End-of-input also aborts.

`--yes` does not answer this per-file question. Binaries, libraries and data
are not hashed at uninstall, so a hand-patched binary can be removed without
a question. Use `verify` and preserve anything you need before approving.
The [uninstall reference](~peios/peipkg/upgrade-and-removal/uninstall) describes
these rules and database-integrity warnings.

### Removing something that is depended on

peipkg will not, by default, leave the system inconsistent. If you ask to remove a package that another installed package depends on, the plan is refused: peipkg tells you what still needs it, and stops.

| Option | Effect |
|---|---|
| `--cascade` | Also remove every installed package that depends on the ones named. |
| `--dry-run` | Print the plan and stop. |
| `--yes`, `-y` | Skip the `proceed?` prompt. |

`--cascade` turns that refusal into a wider plan: peipkg computes the full set of packages that would be left with a broken dependency and adds them to the removal. The plan then shows everything that will be removed. Review it before approving, because a cascade can reach further than expected. There is no implemented system-critical-package guard: even removing the package manager is an ordinary removal. Do not use a cascade as a shortcut around a dependency you have not identified.

```
$ peipkg remove --cascade libfoo
the following changes will be made:
  remove     toolA 2.1
  remove     toolB 1.0
  remove     libfoo 3.3
proceed? [y/N]
```

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — or, for `--dry-run`, the plan was produced. A declined prompt is also `0`: nothing failed. |
| `1` | The operation failed — a package was not found, a dependency could not be satisfied, a download or verification failed, or a file operation was denied. |
| `2` | A usage error — an unknown command or a malformed option. |

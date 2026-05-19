---
title: Installing and removing packages
type: reference
description: install puts packages on the system and remove takes them off. This page covers the plan-and-confirm flow both share, installing straight from a local .peipkg file, and what happens when you remove a package something else depends on.
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/dependency-resolution
  - peios/package-management/transactions-and-recovery
---

`peipkg install` puts packages on the system; `peipkg remove` takes them off. They are the two commands you reach for most, and they share one flow — peipkg works out the full set of changes, shows it to you, and waits for your approval before touching anything.

```
$ peipkg install nginx
$ peipkg remove oldtool
```

## Installing packages

```
peipkg install <package|file.peipkg>...
```

Each argument is either the **name** of a package to fetch from a configured repository, or the **path** of a local `.peipkg` file (recognised by its `.peipkg` suffix). You can mix the two in one command.

Installing a package rarely means installing just that package. peipkg works out everything the request implies — the dependencies the package needs, and *their* dependencies — and presents the whole set. How that set is computed is the subject of [Dependency resolution](~peios/package-management/dependency-resolution); this page is about the flow around it.

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

Nothing has been downloaded and nothing on the system has changed. peipkg waits for an answer. Anything other than `y` or `yes` — including pressing Enter, or end-of-input — is a refusal, and the command exits having done nothing.

Answer `y` and peipkg carries the plan out as a single [transaction](~peios/package-management/transactions-and-recovery): it downloads and verifies every package, then commits the change atomically.

| Option | Effect |
|---|---|
| `--dry-run` | Produce and print the plan, then stop — never prompt, never change anything. |
| `--yes`, `-y` | Skip the `proceed?` prompt and apply the plan. |

`--dry-run` is the safe way to see what a command *would* do. `--yes` is for scripts and unattended runs — but note that it skips only the *routine* prompt. A plan that contains an action needing deliberate authorisation will still stop and ask; `--yes` does not override that. See [Elevated authorisation](~peios/package-management/dependency-resolution) for which actions those are and why.

### Installing from a local file

When an argument is a path ending in `.peipkg`, peipkg installs that file directly:

```
$ peipkg install ./nginx-1.27.4.peipkg
```

This is a **raw install**, and it differs from a repository install in one specific way: it skips the repository **trust layer**. There is no signed index to check the file against, no signing key to verify it under, and none of the freshness or rollback protection a repository provides. You are vouching for the file yourself.

Everything else still happens. The **package format is fully verified**: the archive structure, the manifest, the integrity manifest, and the hash of every payload file are all checked before anything is staged. A corrupt or truncated `.peipkg` is rejected exactly as it would be from a repository. And the file's **dependencies still resolve normally** against your configured repositories — a locally-installed package can pull in repository packages to satisfy what it needs.

A package supplied as an explicit local file takes precedence over any repository's version of the same package, so `install ./foo.peipkg` installs *that* file even if a repository offers `foo` too. In the plan, a local-file operation is marked so the choice is visible:

```
  install    nginx 1.27.4  (local file)
```

In the future, peipkg will be able to consult system policy to decide whether raw installs are permitted at all, and that gate will be configurable. For now a raw install is always allowed; the verification above is what stands behind it.

## Removing packages

```
peipkg remove <package>...
peipkg uninstall <package>...
```

`remove` and `uninstall` are the same command. Each argument names an installed package; peipkg plans the removal — the files to take off disk — and runs the plan-and-confirm flow described above.

A removal leaves shared directories in place and removes only the files the package owns. peipkg knows exactly which files those are from its database, so a removal is clean and complete.

### Removing something that is depended on

peipkg will not, by default, leave the system inconsistent. If you ask to remove a package that another installed package depends on, the plan is **refused** — peipkg tells you what still needs it, and stops.

| Option | Effect |
|---|---|
| `--cascade` | Also remove every installed package that depends on the ones named. |
| `--dry-run` | Print the plan and stop. |
| `--yes`, `-y` | Skip the `proceed?` prompt. |

`--cascade` turns that refusal into a wider plan: peipkg computes the full set of packages that would be left with a broken dependency and adds them to the removal. The plan then shows *everything* that will go — review it before approving, because a cascade can reach further than expected.

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

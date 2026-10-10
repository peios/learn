---
title: Package Manager
type: how-to
description: Install, update and remove software on the desktop with Package Manager, which runs peipkg as you and puts each of its questions to you as it asks it, and what each of its sections does.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/keeping-a-system-current
  - peios/package-management/repositories-and-trust
---

**Package Manager** is the desktop's window on peipkg. Open it from the
launcher (type `package`). It has no authority of its own: it runs
`peipkg` as you, so what you may install or remove is exactly what you
could with the command, and every change is the same transaction, with
the same history and audit record.

## Sections

| Section | Shows | Does | The command |
|---|---|---|---|
| **Installed** | Every installed package, searchable, with its version and where it came from | Opens one: its details, what it needs and provides, and its files. **Check Files**, **Update to…**, **Remove…** | `list`, `info`, `files`, `verify`, `upgrade <name>`, `remove` |
| **Available** | What the repositories offer that isn't installed | **Install**, and **Install from File…** for a `.peipkg` file | `search`, `install` |
| **Updates** | The newer versions waiting, after refreshing the trusted repositories | **Update** one, or **Update All** | `refresh`, `upgrade --dry-run`, `upgrade` |
| **History** | Every change, newest first, by what it did | **Undo…** the most recent, and **Resolve** an interrupted one | `history`, `undo`, `recover` |
| **Repositories** | Each repository, its address, how many packages it offers, when it was refreshed, and whether it is out of date or not yet trusted | **Refresh All**, **Add Repository…**, **Trust…**, **Remove…** | `repo list`, `refresh`, `repo add`, `repo remove` |
| **Roles** | Each [claim](~peios/package-management/claims), what holds it, and its links | Choosing another package moves the claim to it | `claim` |
| **Installation Roots** | The [named roots](~peios/package-management/named-roots) | Nothing: roots are added with `peipkg root` | `root list` |

## Making a change

Every change goes the same way, on one page:

1. **The plan.** What will be installed, updated, moved back or removed,
   with sizes, before anything happens.
2. **Each elevated action, on its own.** A downgrade, a low-trust package
   filling a high-trust role, or a package taking over another's files
   needs your specific approval. Each is asked with **Allow This**, and
   **Cancel** is the keyboard's. Your approval is recorded in the audit
   stream, as it is at a terminal.
3. **The plan's own question:** **Install**, **Update**, **Remove** or
   **Undo**. For a removal, **Cancel** is the keyboard's.
4. **Progress**, through downloading and checking, preparing, putting the
   changes in place and recording them.
5. **The outcome**, with anything peipkg warned of under **Notes**.

A removal can stop partway to ask about a configuration file you changed
since it was installed: **Keep It** leaves it in place, belonging to no
package; **Delete It** removes it and keeps a copy beside it; **Stop
Everything** cancels the removal.

Once you approve the plan, the change finishes even if you close the
window.

## When peipkg refuses

Some refusals have a way on, which Package Manager offers once:

- **A repository's information is out of date**, and refreshing it
  brought nothing newer. **Continue Anyway** carries on with what this
  machine already has, as `--allow-stale` does, and is recorded. Package
  Manager remembers it for its update checks until you close it.
- **A file is in the way:** one the change would install is already there
  and belongs to no package. **Replace It** keeps the file that's there
  beside the new one, as `--overwrite-unowned` does.
- **This is updated another way:** the package's publisher says it is
  updated by other means. **Update Anyway** is `--bypass-alternate-upgrade`.
- **A repository isn't trusted yet:** it is set up on this machine, as an
  image sets up its own, but its trust has never been confirmed.
  **Repositories** takes you to it, where **Trust…** shows the signing key
  given for it and runs the trust ceremony when you confirm, as
  `peipkg repo add <name>` does.

Package Manager never confirms a repository's trust for you, including
when it refreshes repositories to look for updates: it refreshes only
those already trusted.

## What you may do

Package Manager asks the system rather than guessing. If you may not read
peipkg's records, every section says so once and shows nothing more; as
shipped, only Administrators may. If you may read them but not change
them, everything is shown and nothing can be changed, with the reason
said once under each section's heading.

## Where to go next

- [Installing and removing packages](~peios/package-management/installing-and-removing)
- [Keeping a system current](~peios/package-management/keeping-a-system-current)
- [Repositories and trust](~peios/package-management/repositories-and-trust)
- [The driven mode](~peios/peipkg/the-tools/the-driven-mode), for a program
  of your own that runs peipkg the same way

---
title: Prior Art
description: Where this chapter sits against freedesktop desktop entries, Windows' shortcuts, App Paths and registered applications, MSIX manifests and Atrium's catalogue, and which resemblances are deliberate.
---

## The freedesktop desktop entry specification

This chapter is, in outline, a desktop entry: one small file per
application, installed by its package into a shared directory, with a
name, an icon, an executable and the MIME types it handles. `title` is
`Name`, `icon` is `Icon`, `opens` is `MimeType`, and `listed = false`
is `NoDisplay=true` without the double negative.

What it drops is `Exec`. A desktop entry's `Exec` is a command line
with its own quoting rules and a set of field codes, `%f`, `%F`, `%u`,
`%U`, `%i`, `%c`, `%k`, that every consumer must parse and expand, and
that have been the source of most of the specification's errata and
several of its security advisories. This chapter has `program`, an
absolute path, and `arguments`, an array that is passed as it is, with
the file last. There is nothing to parse and nothing to expand.

It also drops `Categories`, `Keywords`, `Actions`, `TryExec`,
`Terminal`, `StartupNotify` and the localised forms of every key,
along with `update-desktop-database` and the `mimeinfo.cache` it
builds. A first version needs a title, a program, an icon and the
types it opens, and a directory that is its own index.

## Windows

Windows has three answers to what an application is, and this chapter
takes something from each. A Start Menu shortcut is a file in a shared
directory whose presence is the listing, which is the shape of §5.4.
`App Paths` in the registry lets a name resolve to an absolute path
without a `PATH` lookup, which is why `program` is absolute. Registered
applications and `Default Programs` let a program say what it opens,
which is `opens`, though the default that Windows keeps beside it is
left to a later version here.

What this chapter does not take is the registry as the place. Peios
has a registry and does not use it for this, because a package installs
files, and a file is present or it is not: there is no second thing to
keep consistent with the first.

## MSIX

An MSIX manifest declares an application's entry point, display name
and visual assets in one document the package ships, and the package
manager reads it at install. That is the shape of a declaration, kept
as a file the package installs rather than something the package
manager extracts, so that presence is enough.

## Atrium

Atrium, Peios' web shell, has its own catalogue: one directory per web
application under `/usr/share/atrium/apps/`, a `manifest.toml` in each,
and "nothing runs at install and nothing registers: presence is the
catalogue." This chapter keeps that sentence and its consequences, and
takes TOML from it. It keeps Atrium's rule that the directory's name is
the id, as the rule that the file's name is the id, and drops the `id`
key that could disagree with it. Atrium's applications are documents
and not processes, so its manifest says which document to load where
this one says which program to run, and its icon is a file in the
directory where this one is a name for PGSS Icons to resolve.

## Design influences

**A declaration, not a place.** An application is what a file says it
is, and not where a binary sits. A program can be a command and an
application at once, a wrapper or a script can be an application, and
nothing about a program's path has to change for it to become one.

**Matched by file, named by path.** A running process is matched to its
declaration by the file it runs, and never by its name, so that no
program can borrow another's title by being called the same thing. A
declaration names its program absolutely for the same reason.

**Data, never a command line.** The one thing every consumer does with
a declaration is start a process from it, often because something
untrustworthy asked. Passing the program and arguments through exactly
as installed is what makes that safe, and is why there are no
placeholders, no shell and no lookup.

**One directory that is its own index.** As with PGSS Icons' themes,
the flat directory is chosen so that no state has to be built,
rebuilt or kept consistent, and so that a package's install and remove
are the whole of the provider's work.

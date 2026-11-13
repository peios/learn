---
title: Publishing
description: What publishing a repository writes, leading and what it leaves out, snapshots that never change, and taking a version back by yanking or deleting it.
---

**Publishing** writes a repository's catalog and `leading` from what it
holds, and signs a new pointer file one higher in sequence.

## The catalog

The catalog lists every version the repository's refs hold, each current or
yanked as the previous catalog had it, and every version a previous catalog
recorded as deleted.

## Leading

`leading` holds, for each package name and architecture, the newest current
version. A package whose dependencies or requirements `leading` can't
satisfy MUST be left out of it, and so MUST anything left needing it,
repeating until what is left can all be installed from it. A publisher MUST
say what it left out and why, and MAY refuse to publish instead.

## Snapshots

A snapshot is a new index holding what an index or channel holds,
`leading` by default. A snapshot never changes: its name MUST be new. To fix
a release, publish a new snapshot and move the release's channel to it.

## Yanking

Yanking a version marks it `yanked` in the catalog: new resolutions don't
choose it, but a request for exactly it still does (§5.29). Republishing
keeps the mark, and unyanking removes it. `leading` doesn't hold a yanked
version.

## Deleting

Deleting a version removes its ref, its manifest, and every blob of it that
no other manifest names, and records it in the catalog as `deleted` with a
reason. A resolution it would have satisfied fails with that reason
(§5.29), so that a missing package is never mistaken for a broken mirror.

A snapshot that holds a deleted version isn't changed. To keep a release
installable, publish a new snapshot without it. Deletion reaches the
repository, not machines: a machine that holds the package keeps it until a
closure without it replaces the one that has it.

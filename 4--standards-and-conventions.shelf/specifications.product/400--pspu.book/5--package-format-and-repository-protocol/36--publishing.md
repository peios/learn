---
title: Publishing
description: What publishing a repository writes, leading and what it leaves out, snapshots that never change, taking a version back by yanking or deleting it, and exporting a copy with compressed blobs.
---

**Publishing** writes a repository's catalog, its provides tree and
`leading` from what it holds, and signs a new pointer file one higher in
sequence. It writes each version's summary (§5.31) for the catalog to
give, and writes again, with summaries, any snapshot written without them;
a snapshot holds the same versions as before.

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

## Exporting

An **export** is a copy of a repository, to serve, whose blobs are
compressed (§5.12). It holds what the repository held when it was last
published: its tree nodes, manifests and refs as they are, every blob
compressed, and a pointer file with the repository's sequence, the line
`blobs zstd`, and a signature by the repository's key. The pointer file
MUST be written after everything it names, and what the repository doesn't
hold, such as a version deleted, removed from the export after it.

An export is written again after each publication. A publisher need not
compress again a blob the export holds already. A publisher MUST NOT write
an export from a publication with a lower sequence than the export has.

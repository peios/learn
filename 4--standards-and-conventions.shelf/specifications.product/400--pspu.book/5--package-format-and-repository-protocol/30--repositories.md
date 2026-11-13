---
title: Repositories
description: An artifact directory that publishes what it holds, its catalog of every version, its indexes of one version of each package, its channels, and the one file that says what each is.
---

A **repository** is an artifact directory (§5.10) that publishes what it
holds. Besides its packages it has:

- a **catalog**, every version it has published, with how each stands;
- **indexes**, each one version of each package for each architecture: the
  index `leading`, the newest, and **snapshots**, each a release's,
  unchanged for ever;
- **channels**, each following an index or another channel, such as
  `stable` or `2026.10`;
- a **pointer file**, the one file of it that changes, which says what the
  catalog, each index and each channel are, and its **signature**.

## Layout

| Path | Holds |
|---|---|
| `repository` | The pointer file (§5.32) |
| `repository.sig` | Its signature (§5.33) |
| `trees/sha256/<hash>` | The nodes of the catalog's and the indexes' trees (§5.31) |
| `blobs/`, `manifests/`, `refs/` | Its packages, as any artifact directory's (§5.10) |

Everything below the pointer file is named by its hash, and is reached from
the pointer file through hashes. A signature over the pointer file therefore
vouches for every tree node, every manifest a tree names and every blob a
manifest names.

## Indexes and channels

Indexes and channels share one namespace, and each name follows §5.9. A
channel's target is an index or another channel, and following channels MUST
reach an index, without a loop.

A release usually has three levels: a snapshot of each patch release, such
as `2026.10.0` and `2026.10.1`; a channel for the release, `2026.10`,
following its latest snapshot; and a channel such as `stable` following the
newest release's channel. A machine tracking `stable` follows every release,
one tracking `2026.10` gets only its fixes, and one tracking `2026.10.0`
changes only when told to.

## Package names belong to one repository

A machine that fetches from several repositories (§5.35) MUST take each
package name from only one of them. A name that two of them publish is an
error, for a request or anything it needs, until the machine is told which.

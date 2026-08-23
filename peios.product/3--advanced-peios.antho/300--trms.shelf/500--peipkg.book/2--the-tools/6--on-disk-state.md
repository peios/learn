---
title: On-Disk State
description: The four kinds of state peipkg keeps across three places — the database, repository configuration, the index cache, and staged files.
---

peipkg keeps four kinds of state, in three places.

## The package database

One transactional store, holding everything in §2.5. It is the
authoritative record of what is installed.

## Repository configuration

One file per repository, in a configuration directory. Each declares the
repository's base URL, its trust anchors, its signature policy, its
priority, and two tuning values: a minimum acceptable index version, and
a maximum trusted age.

The configuration file is the operator's; the recorded trust state — the
verified descriptor, its keys and statuses, and the freshness floor —
lives in the database. Adding a repository writes both. Removing one
deletes both, and leaves installed packages alone.

Configuration is read with no authorisation check of its own. The
security descriptor on the configuration directory is what decides who
may change a repository's transport policy or its trust anchors.

## The index cache

Fetched indexes and their signatures are cached, content-addressed, with
a small pointer file naming the current object for each repository.
Caching avoids re-parsing; it does not avoid re-verifying. Every
operation that relies on a cached index verifies its signature again,
and cross-checks its version and generation timestamp against the
freshness floor recorded in the database.

`peipkg clean` removes cache objects no pointer references.

## Staged files and backups

Neither is a separate directory. A staged file is written as a sibling
of its destination, in the destination's own directory, under a name
carrying the transaction identifier; a backup is a displaced original
renamed to a sibling under a similar name.

Both choices follow from the same requirement: the rename that commits a
file is intra-directory, so that it is atomic and cannot fail with
`EXDEV` because the staging area is on a different filesystem. Backups
additionally cost no disk space, because nothing is copied.

Where a destination's basename is long enough that adding the marker
would exceed the filesystem's name limit, the basename is truncated to
fit.

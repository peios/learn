---
title: The Index Cache
description: Indexes change when a repository publishes but are read on every operation — the cache that closes the gap, and how it is re-verified.
---

Indexes change when a repository publishes; peipkg reads them on every
operation. The gap between those two rates is what the cache exists for.

## Structure

A fetched index and its signature are stored as content-addressed
objects, with a small pointer file naming the current object for each
repository. An older sidecar layout is still read, so a cache written by
an earlier version stays usable.

`peipkg clean` removes objects no pointer references.

## Re-verification

Caching avoids re-parsing JSON. It does not avoid re-verifying
signatures. Every operation that relies on a cached index verifies its
detached signature again against the repository's current trust state.

peipkg additionally cross-checks a cached index against the freshness
state recorded in the database, and rejects one whose index version or
generation timestamp disagrees with what was recorded.

> [!NOTE]
> The two checks close different holes. Re-verifying the signature stops
> substituted metadata being trusted between the cache write and the
> next read. The cross-check against recorded state stops an older
> *validly signed* index being dropped directly into the cache, which
> would otherwise bypass the refresh path where the freshness floor is
> enforced.

## When the cache fails

A cached index that fails to load or fails to verify produces a warning,
and resolution proceeds without that repository.

For a repository the system depends on, that means a package the
operator expected to come from it is instead resolved from wherever else
it is available, at a lower priority.

## Protection

The cache is written with ordinary file permissions and carries no
security descriptor of its own. Its integrity rests on the
re-verification above rather than on who can write to it.

---
title: An Unreachable Repository
description: Fetch failure during a refresh or an install — why the previous trust state is retained and nothing falls back to unverified.
---

## During a refresh

The fetch fails, the failure is reported, and the previous trust state
is retained untouched. peipkg does not fall back to unverified state and
does not silently proceed.

`peipkg refresh` reports each repository's failure and exits non-zero.

## During an install

If the repository's trust state is within its maximum age, the cached
index is used and the operation proceeds normally.

If it has aged out, peipkg attempts a refresh first. A failed refresh —
or a refresh that returns the same index it already had — refuses the
operation, unless the operator passes `--allow-stale`.

Uninstall and undo are not gated this way, so removing something and
reverting a change still work offline.

## When the cache is unusable

A cached index that fails to load or fails to verify produces a warning,
and resolution continues **without** that repository.

The consequence is worth watching for: a package the operator expected
from that repository is resolved from wherever else it is available, at
a lower priority, with only a warning to say so.

## When a repository has been removed

Packages installed from it stay installed, and their recorded origin
stays with them. They are not marked, not flagged in query output, and
not refused for upgrade.

Because their origin no longer resolves to a configured repository, the
cross-repository guards do not fire for them (§3.7).

---
title: Revalidation
description: The caching the specification permits, the version tuple and identity comparison it rests on, and what always invalidating costs.
---

The specification permits an implementation to cache resolutions,
subject to a version tuple recorded per stratum and an identity
comparison on reuse. This implementation caches nothing, and so
implements neither.

## Always invalidate [*coherency.revalidate.always-invalidates]

`d_revalidate` returns 0 for every dentry except the mount root. The
VFS therefore discards the dentry and re-enters `lookup` on every path
walk, and the lookup re-resolves the parent and the child from their
relative path strings across every stratum.

Nothing is memoised. No version value is recorded, no directory
identity is retained for comparison, no nearest-existing-ancestor walk
happens, and no `i_version` is read anywhere in the filesystem. The
per-dentry provider path that is retained is not a cache of a
resolution: it is dropped when the dentry is released, and the dentry
is released on the next walk.

The specification's machinery exists to know when a cached resolution
has gone stale. With no cached resolution, the questions it answers do
not arise:

| What the tuple would detect | Why it is unnecessary here |
|---|---|
| A stratum gaining or losing a name | The next walk resolves the name afresh |
| A stratum's directory appearing | The next walk finds it |
| A stratum's directory removed, renamed away, or renamed over | The next walk finds nothing, or finds the replacement |

The result is strictly stronger than the specification requires, in the
safe direction. The two internal counters the superblock does carry —
the inode-number allocator and the staging-name counter — are consulted
by nothing in this path.

## What it costs [*coherency.revalidate.rcu-walk-refused]

The cost is real and lands on the hottest path in the kernel.

`d_revalidate` refuses RCU-walk unconditionally: a lookup in RCU mode
returns `ECHILD` and the walk is retried in ref-walk mode, and the
directory permission check does the same. RCU-walk is therefore never
used on a stratafs mount, and the fallback is taken always rather than
only where it genuinely cannot proceed.

The refusal, invisible to the caller by design, is visible at two
tracepoints. `stratafs:stratafs_rcu_walk_refused` marks the directory
permission check turning a walk back under `MAY_NOT_BLOCK` — in
practice the first stratafs directory a walk must traverse does this,
so it is the point that actually takes every walk out of RCU mode.
`stratafs:stratafs_d_revalidate` records each revalidation verdict —
mount cookie, merged inode number (zero for a negative entry), whether
the call was in RCU mode, and the return value — and because the
permission check fires first, every recorded call arrives already in
ref-walk mode; its `-ECHILD` branch is the backstop. Like every PKM
tracepoint, neither records a pathname.

What replaces it, per path component, is one full `filename_lookup` per
stratum — up to sixteen — plus one merged resolution per proper prefix
of the path, for the ancestor-masking test of §4.3.3. Where a mount is
established over a directory of executables, that lies on the path of
every program execution, and there is no dentry cache hit to avoid it.

This is the one part of the filesystem whose cost is worth measuring
rather than assuming, and closing the gap — recording enough per
resolution to reuse one safely, and making the comparison RCU-safe — is
tracked as work in its own right.

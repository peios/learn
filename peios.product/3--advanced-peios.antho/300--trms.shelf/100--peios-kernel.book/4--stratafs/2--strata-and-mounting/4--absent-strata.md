---
title: Absent Strata
description: A stratum's directory may not exist — what happens while it is absent, and what appearing, disappearing and reappearing do.
---

A stratum's directory may not exist. It may be absent when the mount is
created — which requires `am` (§4.2.3) — or exist at mount time and be
removed while the mount is live, which nothing prevents for any
stratum.

## While absent

An absent stratum holds no names, participates in no merged directory,
and contributes no entries to any enumeration. It keeps its position
and its precedence; only its presence bit is clear.

The mechanism is a single test in the resolver. Resolving one stratum
either succeeds, or fails with `ENOENT` or `ENOTDIR`, in which case the
stratum is skipped and its bit is left clear. Any other error —
`EACCES`, `EIO`, `ELOOP`, `ENAMETOOLONG`, `ESTALE` — is not treated as
absence and fails the whole resolution instead. So a stratum that is
unreadable for a reason other than not being there masks the name for
every stratum, rather than being passed over.

An absent create stratum additionally causes every operation that would
create or copy up to fail with `EROFS`. The create stratum's root is
re-resolved at the point of use and its `ENOENT` is mapped to `EROFS`
by each of the paths that needs it — the copy-up parent walk, the
creation authorisation pre-check, and the routing decision, which
computes create-stratum presence live and requires the result to be a
directory. stratafs does not create the stratum's own directory to
satisfy such an operation: establishing that directory, with the
security descriptor it should have, belongs to whatever provisions the
system, and a mount that minted it would be choosing that descriptor.

## Appearing and disappearing

Neither event is detected. Both are simply observed, because there is
nothing to invalidate.

A stratum's directory is never held; only its path string is. Every
resolution walks that string afresh, so a directory that comes into
existence is picked up by the very next lookup, and one that is
removed, renamed away, or replaced by another directory is picked up
just as immediately — the walk finds nothing, or finds the replacement.

The specification describes this in terms of a version tuple recorded
over the nearest existing ancestor of an absent stratum's path, and an
identity comparison for a stratum that disappears. Neither exists in
the implementation, and neither is needed: they are the machinery for
knowing when a *cached* resolution has gone stale, and nothing is
cached. §4.4.2 covers the trade that represents.

The `am` flag is not consulted at runtime at all. It governs whether
the mount is allowed to be established with the directory missing, and
nothing more; a stratum without it that vanishes afterwards behaves
exactly like one with it.

## Reappearance

A stratum that disappears and reappears is the same stratum in the same
stack position, and nothing about the old directory is remembered.
Resolutions are recomputed against whatever the new directory holds.

One piece of state does survive the gap, though it is not resolution
memory. The inode-number identity map (§4.4.3) is keyed on the provider
inode object and pins it for the life of the mount, so if the same
underlying inode is reached again — because the directory was renamed
away and back rather than replaced — it receives the same inode number
it had before. That is exactly what the identity rule requires: equal
numbers for one provider object, whatever path reached it.

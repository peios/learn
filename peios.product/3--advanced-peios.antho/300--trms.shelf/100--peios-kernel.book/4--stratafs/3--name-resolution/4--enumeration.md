---
title: Enumeration
description: The union of names across participating strata, each appearing once — captured at open, with consistency and position rules.
---

Enumerating a merged directory yields the union of the names held by
its participating strata, with each distinct name appearing exactly
once.

## Capture at open

The whole listing is built when the directory is opened, and the
enumeration is served from that capture for the life of the descriptor.
Each participant is opened and iterated in ascending stratum order, and
its entries are appended to one list.

Deduplication is global rather than per-stratum: before an entry is
recorded, the whole accumulated list is scanned for the same name, and
a match causes the entry to be dropped. Because participants are
visited highest-precedence first, the entry that survives is always the
provider's. `.` and `..` are dropped from every participant and
synthesised once.

Each surviving entry carries the name, its length, the directory entry
type reported by the providing participant, and an inode number
obtained by looking the child up in that same participant and mapping
the result through the identity table (§4.4.3), so `getdents` and
`stat` agree. The final component is not followed during that lookup,
so a symlink entry reports its own identity rather than its target's.

Two details of that: an entry that vanishes between the participant's
own `readdir` and the follow-up lookup is silently dropped, which is
ordinary provider behaviour; and a participant filesystem that reports
`DT_UNKNOWN` has that propagated unchanged, even though the child path
is in hand and the real type could be derived.

Shadowed entries are neither reported nor otherwise detectable. No
second record is ever allocated, so nothing about them survives into
the listing, and the entry count reflects distinct names only.

The order in which names are reported is stratum-ascending and then
each stratum's own `readdir` order — deterministic for one capture, and
not otherwise specified.

## Consistency

There is exactly one capture per descriptor. Nothing appends to the
list after the directory is opened, and nothing re-captures — a
rewind replays the original capture, since the directory uses the
generic `llseek`. A change to any participating stratum after the open
is therefore invisible to that descriptor for its lifetime.

What that bounds is only what stratafs itself contributes. Each
participating directory is enumerated by its own filesystem, with
whatever consistency that filesystem offers its own callers, and
participants are read sequentially with no cross-stratum lock or
barrier. A merged listing is no better than the listings it is
assembled from, and nothing claims otherwise.

## The settled participant set

For the purpose of enumeration, the participating set is settled when
the directory is opened and does not change for the life of the
descriptor. What is settled is the set of participating **directory
objects**, not the set of stratum positions: the descriptor holds a
`struct path` reference on each participant, pinned until release, and
nothing re-resolves those positions by path. A participant that has
since been removed and replaced by another directory at the same path
is a different object and contributes nothing.

The settled set has exactly three consumers: the enumeration itself,
the access check performed when the directory is opened (§4.6.2), and
the origin attribute read through that descriptor (§4.7). It extends to
nothing else. Resolving a name relative to the descriptor — opening,
removing, renaming, linking — is an ordinary live resolution under
§4.3.1, performed against the strata as they are at that moment.

So a descriptor opened before a stratum began to hold the directory
will not list that stratum's names, but `openat` through the same
descriptor will resolve them. The two answers differ deliberately:
enumeration is a bulk disclosure whose authorisation was decided once,
when the descriptor was opened; a resolution is a fresh operation that
carries its own check.

Freezing the participant set is what keeps that open-time check
meaningful. Were a later re-read free to admit a stratum that joined
afterwards, its names would reach the caller without its directory's
descriptor ever having been consulted — and a stratum owner could make
a directory participate precisely to expose it. A caller that wants the
current participant set reopens.

## Positions

Offsets 0 and 1 are `.` and `..`. Offset `2 + k` is the k-th element of
the captured list — a plain ordinal. The offset each participant
filesystem supplies is discarded: no provider cookie, no stratum index,
and no name hash is encoded.

A position is therefore meaningful only within one open file
description. On close and reopen — and so across a remount or a reboot —
the capture is rebuilt from each stratum's current contents and current
`readdir` order, and ordinal `2 + k` may name a different entry or
none. `telldir` and `seekdir` across descriptors are unreliable on a
stratafs directory, as is NFS re-export of one.

## Access

Enumeration requires traverse and list rights on **every** participating
directory, checked before the capture is built. The check returns on
the first refusal, and a refusal aborts the open entirely, so no
partial listing covering only the readable strata can be produced.

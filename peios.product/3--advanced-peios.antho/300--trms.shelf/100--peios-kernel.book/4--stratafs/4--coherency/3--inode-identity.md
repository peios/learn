---
title: Inode Identity and Lifecycle
description: stratafs allocates its own inodes standing for provider objects — the identity it reports, the mount root, and what a provider change does.
---

stratafs presents its own inodes, allocated from its own superblock.
Each stands for a provider object and forwards operations to it; none
holds file data, directory entries, or a security descriptor.

## Reported identity [*inode.number-allocated-not-derived]

The device identifier reported for any object in a mount is the
stratafs superblock's own anonymous device, not the provider's.
`getattr` calls the provider's directly and then overrides `dev`, `ino`
and, for directories, `nlink`; all four inode-operations tables install
that same `getattr`, so there is no path around it.

The inode number is **allocated, not derived**. A per-mount monotone
counter hands out a number for each distinct provider inode the first
time it is seen, and the pair is recorded in an `xarray` on the
superblock keyed on the provider inode, holding a reference on it so
the object cannot be freed and its address reused while the mount
lives. The counter starts at 1 and is pre-incremented, so the first
number handed out is 2. The provider's own inode number and device are
never read for this purpose.

That satisfies the identity requirements — two names compare equal
exactly when they resolve to one provider object, since the map is
keyed on the object itself and not on the stratum that reached it, so
hard links compare equal and one directory reached through two strata
compares equal too. It does not follow the specification's advice to
derive the number from the provider's, and it therefore pays the cost
that advice exists to avoid: the map is never evicted from, and it pins
every provider object ever reached through the mount until unmount. A
mount whose strata would not have provoked the fallback pays it anyway.

Two mechanical details. The map key is the provider inode's kernel
address shifted right by three; a collision would be caught by the
stored back-pointer and turned into an allocation failure rather than a
false equality, so it fails rather than lying. And the stored number
and `i_ino` are `unsigned long` while the counter is 64-bit, so on a
32-bit build the number truncates.

### The mount root [*inode.root.number-fixed-attributes-live]

The root inode is created once, when the superblock is filled, and its
number is never recomputed — `d_revalidate` returns 1 for the root, so
it is never replaced. Its provider *is* re-resolved live on every use,
so the root's mode, owner and timestamps are always current; only the
number is not.

When the root's provider changes — a higher-precedence stratum root
appears, or the mount-time one is removed — `stat` on the mount point
keeps reporting the number allocated for the mount-time provider. Where
no stratum root existed at mount, it reports a bare counter value
corresponding to no provider object at all. If the root's current
provider is also reachable at some other merged path, that path reports
the object's mapped number while the root reports its stale one, so two
paths naming one object disagree. This is tracked as a defect.

## Attributes of merged directories [*inode.merged-dir.attributes-from-provider]

A merged directory's owner, group, mode and timestamps are its
provider's — the highest-precedence participating directory — taken
straight from a `getattr` on the provider path, so what is reported is
a real directory's attributes rather than a composite.

Its link count is forced to 1, both in the cached inode and in the
reported `stat`. The true count of subdirectories spans strata and [*inode.merged-dir.nlink-forced-to-1]
cannot be maintained, so the value carries no meaning beyond indicating
that the object is a directory. Nothing should infer a subdirectory
count from it.

The security descriptor of a merged directory is not a single
descriptor; §4.6.2 defines which participating directory's descriptor
governs each operation.

## Provider change [*inode.never-rebound-by-resolution]

When the provider for a path changes — because a higher-precedence
stratum gained the name, because the previous provider's entry was
removed, or because copy-up produced a new object — a **resolution** of
that path yields a new inode. An inode reached by resolution is never
re-associated with a different provider.

That is required because per-inode state is populated from the provider
the inode was resolved against and is not in general re-derivable. In
particular KACS caches a security descriptor against the outer stratafs
inode; applying it to a different provider's object would govern access
to one object by another object's descriptor.

The implementation enforces this bluntly. The one function that
re-associates an inode with a new provider is reachable from exactly
one call site, on the descriptor-private dentry created at open, and
never on a hashed dentry reached by resolution. A copy-up performed for
a path rather than a descriptor drops the dentry instead of rebinding
it. Provider change by masking or removal needs no special handling at
all, because the unconditional invalidation of §4.4.2 forces a fresh
lookup and a fresh inode.

An object's reported inode number therefore changes when its provider
changes. That is expected: it is the same change a caller would observe
if the file had been replaced, which is what has happened.

### Descriptors already open [*inode.copy-up.descriptor-keeps-inode]

A descriptor open at the moment its own operation copies its object up
is not re-pointed. It keeps the inode it was opened against, and that
inode's backing object becomes the copy: the provider path and provider
inode are swapped in place under a per-inode lock, the attributes are
refreshed, and the backing file is replaced, so subsequent operations
through the descriptor reach the copy.

This is the one case in which an inode's backing object changes, and it
is safe for the reason the general rule exists: copy-up preserves the
source's security descriptor exactly (§4.6.3), so the descriptor cached
on that inode remains correct for the copy.

At open, the descriptor-private inode is deliberately given the path
inode's number, so before any copy-up `fstat` and `stat` agree. After
one they do not: the descriptor keeps the number allocated for the
pre-copy-up provider, while a fresh resolution of the path allocates a
number for the copy. Both name the copy; the numbers disagree for as
long as that descriptor lives. §4.8 records it.

## Lifetime [*inode.pins-provider-until-unmount]

A stratafs inode holds a reference on its provider inode for as long as
it lives, released on eviction. The dentry additionally holds a full
path reference, and the identity map a third, held until unmount.

Releasing the last reference to a stratafs inode modifies nothing:
eviction truncates its own empty mapping, clears the inode, drops the
provider reference, and frees its private state.

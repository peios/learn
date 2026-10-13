---
title: Inode Identity and Lifecycle
description: stratafs allocates its own inodes standing for provider objects — the identity it reports, the mount root, and what a provider change does.
---

stratafs presents its own inodes, allocated from its own superblock.
Each stands for a provider object and forwards operations to it; none
holds file data, directory entries, or a security descriptor.

## Reported identity [*inode.number-derived-from-provider]

The device identifier reported for any object in a mount is the
stratafs superblock's own anonymous device, not the provider's.
`getattr` calls the provider's directly and then overrides `dev`, `ino`
and, for directories, `nlink`; all four inode-operations tables install
that same `getattr`.

The inode number is derived from the provider filesystem's reported
inode number and a small mount-local identifier for its reported device.
The device identifier distinguishes filesystem domains, not stratum
positions: a stratum can cross mount points. The reported device also
distinguishes Btrfs subvolumes, which can share a kernel superblock and
inode numbers. Two paths to the same provider identity, including hard
links and bind-mounted aliases, therefore report the same number.

Derivation reserves the high bit for allocated fallback numbers. A
self-delimiting tag in the low bits identifies the filesystem domain;
the provider inode number occupies the remaining bits. Small provider
numbers stay small enough to derive again through nested stratafs views.
Neither the bit layout nor the mount-local domain assignment is a
persistent identifier or an ABI that callers should decode. Numbers
may differ between mounts; within a mount, reloading the same provider
identity after cache eviction produces the same number.

Only identities that cannot fit, or providers that do not report a
usable inode number, use the fallback map. It allocates a distinct
number and holds a reference on the provider inode until unmount to
prevent address reuse. Repeated encounters with that provider reuse its
allocation. Synthetic provider-less roots use the same allocated number
space without a provider reference. Exhaustion returns `EOVERFLOW`
rather than wrapping, including on 32-bit builds. An attribute lookup
error is returned to the caller instead of silently assigning a new
identity.

### The mount root [*inode.root.follows-live-provider]

The root inode is created once, when the superblock is filled, and the
root dentry is never replaced — `d_revalidate` returns 1 for it. Its
provider is nevertheless re-resolved live on every use, and the number
follows: resolving the root's provider derives or looks up its identity
and writes the result to the root inode's number.
Mode, owner, timestamps and number are therefore all current.

That the number follows is what keeps §4.4.3's identity rule true at
the root. Identity belongs to the provider, so the number the root
reports is the number every other merged path to that same provider
reports; without it, a root whose provider is also reachable elsewhere
would report a different number from that other path — two paths naming
one object, unequal. [*inode.root.agrees-with-other-paths-to-its-provider] That is the false-inequality direction, the one
that breaks hard-link detection.

Where no stratum root exists at mount time, the root receives a stable
synthetic number, distinct from derived provider numbers. If a provider
later appears, the root's number follows that provider.
[*inode.root.synthetic-without-a-provider]

## Attributes of merged directories [*inode.merged-dir.attributes-from-provider]

A merged directory's owner, group, mode and timestamps are its
provider's — the highest-precedence participating directory — taken
straight from a `getattr` on the provider path, so what is reported is
a real directory's attributes rather than a composite.

The security descriptor of a merged directory is not a single
descriptor; §4.6.2 defines which participating directory's descriptor
governs each operation.

### The synthetic link count [*inode.merged-dir.nlink-forced-to-1]

Its link count is forced to 1, both in the cached inode and in the
reported `stat`. The true count of subdirectories spans strata and
cannot be maintained, so the value carries no meaning beyond indicating
that the object is a directory. Nothing should infer a subdirectory
count from it.

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
one they do not: the descriptor keeps the number assigned to the
pre-copy-up provider, while a fresh resolution of the path derives or
allocates a number for the copy. Both name the copy; the numbers disagree for as
long as that descriptor lives. §4.8 records it.

## Lifetime [*inode.provider-reclaim-with-live-mount]

A stratafs inode holds a reference on its provider inode for as long as
it lives, released on eviction. The dentry additionally holds a full
path reference. Ordinary derived identities add no provider reference
and no per-inode entry to the identity map. Walking a persistent-backed
view and dropping caches can therefore reclaim the provider inodes while
the stratafs mount remains live. The per-mount device-domain table stays
until unmount; its size tracks encountered filesystem domains rather
than the number of files walked.

The fallback alone adds a provider reference held until unmount. That
cost applies only to identities that could not be derived.

Renaming a provider out of the view and back, or evicting and reloading
its cached inode, preserves its derived identity. [*inode.stable-across-cache-reclaim]
Ordinary inode-number reuse by the provider after deletion remains
possible, just as it is when accessing that filesystem directly.

Releasing the last reference to a stratafs inode modifies nothing:
eviction truncates its own empty mapping, clears the inode, drops the
provider reference, and frees its private state.

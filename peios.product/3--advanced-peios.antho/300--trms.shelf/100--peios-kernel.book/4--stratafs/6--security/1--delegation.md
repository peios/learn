---
title: Access Check Delegation
description: stratafs stores no descriptors and allocates its inodes bare — who performs which access check, and when.
---

stratafs stores no security descriptors. It allocates its outer inodes
bare and never runs the inode security initialisation over them, and
neither its inode state nor its superblock state has anywhere to put a
descriptor. Every object reachable through a mount has its descriptor
on its own stratum, and that descriptor is what governs access to it. [*security.descriptor-on-provider-stratum]

## The rule [*security.check-evaluates-target-descriptor]

An access check for an operation on an object reachable through a
stratafs mount evaluates the security descriptor of the object the
operation will be performed against. For an operation on a
non-directory, that is the provider's object; for a merged directory,
§4.6.2 defines which participants' descriptors apply.

stratafs synthesises no descriptor, supplies none of its own, and
applies no mount-level template. It could not: constructing one would
require a synthesising mount policy class, and stratafs is pinned to
the class that denies where a descriptor is missing (§4.6.4).

Because the descriptor evaluated is the provider's own, a stratafs
mount cannot grant access that the provider's stratum would refuse.
That property is structural rather than a matter of care in
implementation: there is no descriptor for stratafs to get wrong,
because it holds none.

The guarantee is one-directional, which is the direction that matters.
Where the provider carries no descriptor there is nothing to evaluate
and the mount's own policy decides, which is to refuse — so such an
object is unreachable through the mount even where its own filesystem's
policy would have admitted it.

## Who performs which check [*security.merged-checks-are-stratafs-own]

For an object with a single provider, the descriptor comes back through
ordinary forwarding. KACS reads the canonical descriptor attribute the
same way it does for any file, the stacking layer forwards the
`getxattr` down to the provider, and the descriptor that comes back is
the provider's. For metadata and extended-attribute operations, stratafs
re-targets the pending one-shot KACS decision onto the provider inode,
so the check is made against the object the operation will reach.

A merged directory is not that case. It stands for several directories
with several descriptors, and forwarding yields only the provider's.
Those checks are **stratafs's own**: it walks every present
participating directory and evaluates each one's descriptor, failing on
the first refusal.

KACS cooperates by standing down on stratafs inodes entirely. Its
`inode_permission` hook, and its create, mkdir, mknod, symlink, link,
unlink, rmdir and rename hooks, all return success immediately for a
superblock carrying the stratafs magic. The checks that matter are made
by stratafs against the real objects, or by KACS against the real
objects once stratafs has resolved them.

## Timing [*security.open-grant-frozen]

The descriptor evaluated is the provider's at the time the check runs,
and the open-time grant is frozen into the file's KACS state — the
check-at-open principle applies unchanged, and copy-up transfers that
immutable snapshot to the new backing file rather than deciding again.

Two caching seams are worth recording precisely, because the
specification requires the value evaluated to be the provider's
*current* descriptor.

For the merged-directory checks stratafs performs itself, it is exact:
the provider's attribute is re-read on every call, with no cache.

For file opens it is not. KACS caches the resolved descriptor against
the **outer stratafs inode**, and a cache entry sourced from an
attribute read is never revalidated — the only things that replace it
are an explicit descriptor set on that inode and a copy-up install. A
later open of the same outer inode therefore evaluates the descriptor
read at the first open rather than the provider's current one. This is
tracked as a defect.

The second seam is narrower. When copy-up rebinds a descriptor's inode
to the copy (§4.4.3), nothing invalidates that cached descriptor, so
the value retained was literally read from the old provider. No wrong
decision follows, because copy-up preserves the descriptor exactly
(§4.6.3) and the two are equal — but the invariant is held by that
coincidence rather than by the mechanism.

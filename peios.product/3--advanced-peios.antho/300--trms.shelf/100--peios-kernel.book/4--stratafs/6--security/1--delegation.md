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

For merged-directory checks, stratafs reads each participant's descriptor
attribute on every check. KACS also refreshes an outer stratafs inode's
parsed descriptor whenever a check or descriptor query needs it. A writer
using the stratum directly therefore needs no invalidation protocol with
the merged view. Missing and corrupt descriptors are re-read too, so a
subsequent repair can take effect.

This refresh applies to retained handles as well as new pathname operations.
An `O_PATH` handle performs its live access check against the refreshed
descriptor. An ordinary file handle retains its granted access, but a
permitted descriptor query returns the provider's current descriptor, not
the one present when the file opened.

When copy-up rebinds a file's inode to the copy (§4.4.3), stratafs explicitly
invalidates the parsed descriptor. Subsequent descriptor queries follow the
new provider. The file's frozen grant remains unchanged; invalidating the
inode cache does not authorise or revoke access on an already-open file.

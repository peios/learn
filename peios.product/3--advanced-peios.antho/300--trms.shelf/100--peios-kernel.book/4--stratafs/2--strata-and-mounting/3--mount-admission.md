---
title: Mount Admission
description: What a caller must be entitled to and what a configuration must satisfy — evaluation order, loop detection, and mount immutability.
---

A stratafs mount is configured entirely at mount time. This section
covers what the caller must be entitled to, the conditions a
configuration has to satisfy, and the order in which those conditions
are evaluated.

## Entitlement

Establishing a mount with no create stratum takes no privilege of its
own. The filesystem type carries `FS_USERNS_MOUNT`, so an unprivileged
mount in a user namespace is permitted; what the caller needs is only
the access that resolving the stratum paths already requires, which
falls out of the resolution itself. [*mount.unprivileged-without-create]

A stack that carries `create` is different. Copy-up is authorised by
the outer handle and deliberately requires no add-entry right on the
create stratum (§4.6.2), so the mount configuration carries authority
to materialise names in a real directory outside the mount. The caller
establishing such a stack must be operating in the **initial** user
namespace and hold `CAP_SYS_ADMIN` there; anything else fails with
`EPERM`. [*mount.create-requires-init-userns-cap]

The test is made in `get_tree`, before the tree is built and therefore
before any stratum path is resolved, and it is stricter than requiring
the capability alone: the credential's own user namespace must *be* the
initial one, not merely a namespace in which the capability resolves.
This is the closure the KACS copy-up context depends on. The check is
made once, when the immutable stack is established, rather than at each
copy-up, so descriptor delegation cannot reintroduce authorisation
against the acting task, and no reconfiguration can re-supply the
strata list. [*mount.create-entitlement-checked-once]

There is no explicit per-stratum entitlement check in the mount path.
Both halves come out of the ordinary machinery: traverse rights are
enforced by the path walk, which runs under the mounting caller's
credentials, and the right to read a stratum directory's attributes is
enforced by using the security-checking `vfs_getattr` rather than its
unchecked variant, which reaches KACS's `getattr` hook and demands
`FILE_READ_ATTRIBUTES`. [*mount.stratum-rights-from-walk-and-getattr]

One seam is worth recording: the path walk uses the credentials
captured on the filesystem context, while `vfs_getattr` runs outside
that override and so uses the acting task's. For a mount established
the ordinary way the two are the same task. For one established with
`fsopen` and `fsconfig` from different tasks they need not be. [*mount.fsconfig-credential-seam]

Nothing re-checks entitlement if a stratum directory later appears. [*mount.no-recheck-on-appearance]
That is sound because every access through the mount is checked against
the providing object in any case (§4.6.1), so a caller who mounts a
stratum they cannot read still cannot read it.

## Validity

| Condition | Error |
|---|---|
| The stratum stack is empty | `EINVAL` [*mount.admit.empty-stack-einval] |
| The stack exceeds 16 strata | `EINVAL` [*mount.admit.too-many-strata-einval] |
| More than one stratum carries `create` | `EINVAL` [*mount.admit.multiple-create-einval] |
| A stratum carries both `create` and `ro` | `EINVAL` [*mount.admit.create-with-ro-einval] |
| The same directory appears as more than one stratum | `EINVAL` [*mount.admit.duplicate-stratum-einval] |
| A malformed `strata=` value (§4.2.2) | `EINVAL` [*mount.admit.malformed-value-einval] |
| A create-bearing stack from outside the initial user namespace, or without `CAP_SYS_ADMIN` there | `EPERM` [*mount.admit.create-requires-privilege-eperm] |
| A stratum's path names something other than a directory | `ENOTDIR` [*mount.admit.not-a-directory-enotdir] |
| A stratum's directory is absent and the stratum does not carry `am` | `ENOENT` [*mount.admit.absent-without-am-enoent] |
| The composed stack reaches the kernel's maximum stacking depth | `ELOOP` [*mount.admit.stacking-depth-eloop] |
| A stratum lies within the mount point, or within another stratafs mount whose strata include this mount point | `ELOOP` [*mount.admit.recursive-stratum-eloop] |
| Sixteen consecutive collisions allocating a mount cookie | `EAGAIN` [*mount.admit.cookie-exhaustion-eagain] |

Two strata are the same directory when they resolve to the same
directory object, not merely when their paths are equal as strings: the
comparison is on resolved inodes, so two paths reaching one directory
through different symbolic links or bind mounts are caught. Absent
strata are skipped and never compared. [*mount.duplicate-strata-by-inode]

## Evaluation order

The conditions that depend on nothing but the option string are decided
first, during parsing and stack-wide validation, and are reported
whatever the caller's access. The `EPERM` admission test comes next, in
`get_tree`, still before any path is touched. Only then are the strata
resolved. [*mount.admission-evaluation-order]

The purpose of that ordering is to stop the validity conditions being
an oracle: a caller with no right to traverse a directory should not be
able to name it as a stratum and learn from the errno whether it exists
and whether it is a directory.

For a single stratum, that holds. The path walk runs under the caller's
credentials, so a path the caller cannot resolve returns `EACCES` from
the walk itself, before the type test or the duplicate test is reached,
and the `EACCES` is propagated unchanged. [*mount.unresolvable-path-returns-eacces]

Across the stack it does not. The strata are checked in one loop —
resolve, stat, type-test, compare against earlier strata — so stratum 0
is fully judged before stratum 1 is resolved at all. A caller who names
a readable stratum first and an unreadable one second learns the first
stratum's `ENOTDIR` or `ENOENT` rather than the `EACCES` they would
have been given had the whole stack been checked for entitlement first.
This is tracked as a defect; the disclosure is bounded to paths the
caller could resolve, but the specified ordering is stack-wide.

The mount-point loop condition is evaluated in a different call
entirely, after the tree has been built, and so always follows every
entitlement check.

## Loops

A stratum inside the mount point is detected directly. The indirect
case — a stratum inside *another* stratafs mount whose own strata
include this mount point — is detected by recursing into any stratum
whose superblock carries the stratafs magic, bounded by a visited-
superblock set and by the kernel's maximum stacking depth. [*mount.loop-detected-at-mount] This runs
through a Peios-added `super_operations` hook, `validate_mountpoint`,
wired into the new-mount, bind and move-mount paths by the patch series;
it is not an upstream interface.

That check cannot bind after the fact: a mount established within a
stratum, or a bind mount of this mount into one of its own strata, can
create a cycle later. Resolution is guarded separately, and differently
— not by a depth counter but by a per-task, per-superblock re-entrancy
list. A task that is already resolving in a superblock and re-enters it
gets `ELOOP` immediately, so a cycle spanning any number of stratafs
mounts terminates the moment it returns to one it is already inside. [*mount.resolution-reentrancy-eloop]

## Immutability and mount identity

The stack is fixed for the life of the mount; changing one is expressed
by unmounting and mounting again (§4.2.2).

Two stratafs mounts may name the same directory as a stratum. Each
resolves independently and neither is aware of the other; where both
have a create stratum in common they mutate the same objects, with the
same result as any two writers of one directory. There is no registry
of stratum paths to make them aware of each other. [*mount.strata-shared-between-mounts]

There is a registry of *mounts*, but it exists for a different purpose.
Each mount draws a random non-zero cookie and inserts itself into a
global table, retrying up to sixteen times on collision; a second
random non-zero cookie is drawn once per boot. The pair identifies
which live mount owns a staging entry, so that a mount sharing a create
stratum can distinguish another mount's copy-up in flight from an
orphan left by a crash (§4.5.2).

A mount succeeds even when no stratum root is present at all — a stack
whose only strata are absent `am` strata is legal. The root inode is
constructed with no provider, and reports mode `S_IFDIR` with no
permission bits. [*mount.all-absent-stack-is-legal]

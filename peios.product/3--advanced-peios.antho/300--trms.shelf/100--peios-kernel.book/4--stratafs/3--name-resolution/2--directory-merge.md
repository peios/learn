---
title: Directory Merge
description: When lower strata hold the same name as a directory the result is a merged directory — participation, its create stratum, and symlinks.
---

Where a name's provider is a directory, and lower-precedence strata
hold the same name as a directory, the resolved object is a **merged
directory**.

## Participation

The strata participating in a merged directory are, in precedence
order, those whose corresponding directory both exists and is a
directory. A stratum holding the name as a non-directory does not
participate and is masked entirely (§4.3.3); a stratum not holding the
name simply does not participate. [*resolution.merge-participants]

Every consumer of a merged directory applies the same two-part filter —
the presence bit is set, and the resolved dentry is a directory — in a
single ascending loop over stratum indices with a `continue` for
non-participants. Nothing compacts or re-sorts, so relative precedence
within a merged directory is always the relative precedence in the
stack. [*resolution.merge-precedence-follows-stack]

Merging is recursive, and it is recomputed rather than cached: there is
no merged-directory object anywhere. Each lookup and each directory
open rebuilds the full per-stratum path set from the relative path
string, so any child that is a directory in more than one stratum
merges at its own level by the same rule. [*resolution.merge-is-recursive]

The root of a mount is a merged directory whose participants are the
mount's strata. The root has one special case: where the ordinary
provider rule would pick a stratum root that is present but not a
directory, the root instead takes the first stratum that is both
present and a directory, so an absent or non-directory stratum root
cannot change the synthetic root's type. [*resolution.root-type-ignores-non-directory-stratum] A mount whose stratum roots
are all absent still has a root inode, with no provider and no
permission bits. [*resolution.root-exists-with-all-strata-absent]

## The create stratum of a merged directory

A merged directory's create stratum is the correspondingly-named
subdirectory of the mount's create stratum, at the same path relative
to the mount root — whether or not that subdirectory currently exists.
It follows that a merged directory has a create stratum even when the
mount's create stratum holds no part of that path, and creation still
routes there. [*resolution.merge-create-stratum-is-positional]

The derivation is positional and mount-wide: `create_index` is a single
integer on the superblock, fixed at mount, and every creation and
copy-up site reads it directly. Nothing re-derives it from which strata
happen to participate.

That matters because the alternative — taking the create stratum to be
the highest-precedence participating writable directory — would make
the destination of a write depend on which directories happened to
exist, so creating a file in a subdirectory could land in a different
stratum from creating one beside it.

Where the create stratum's counterpart of a merged directory does not
exist, the path is materialised on demand, from the mount root
downwards, at the point an operation first needs it (§4.5.2). [*resolution.merge-create-path-materialised-on-demand] The
authorisation for creating into it is evaluated against the descriptor
that directory will carry once materialised, which is the corresponding
provider directory's (§4.6.2). [*resolution.merge-materialise-checked-against-provider-descriptor]

## Symbolic links and participation

Two resolution entry points disagree about the final component of a
stratum path, and the difference is visible.

Ordinary lookup resolves without following the final component, so a
symbolic link at a name resolves to the link itself and the VFS follows
it. Building the participant set for a merged directory follows the
final component, and so do the emptiness scan, the foreign-entry scan,
the permission check and directory `fsync`. [*resolution.merge-participant-set-follows-final-component]

The consequence is that a stratum holding a name as a symlink to a
directory **participates** in the merged directory, contributing the
target's entries to the merged listing and to emptiness tests, while a
stratum holding a dangling symlink at that name participates in
resolution but not in the participant set. [*resolution.merge-symlink-to-directory-participates] Whether that is intended is
an open question against the specification, which describes a stratum
holding a non-directory as masked; it is tracked as a defect.

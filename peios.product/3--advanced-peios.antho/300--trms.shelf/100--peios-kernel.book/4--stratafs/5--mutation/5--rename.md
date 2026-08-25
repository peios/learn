---
title: Rename
description: Rename both removes and creates, so the source is bound by the removal constraint — atomic replacement, flags and RENAME_NOREPLACE ordering.
---

Rename both removes a name and creates one. Because stratafs cannot
make a name disappear (§4.5.4), the constraint on the source is the
same as for removal, and the constraint on the destination follows from
the read-after-write direction of §4.5.1.

For a rename of a source to a destination within one mount, letting `P`
be the source's provider:

1. `P` must accept modification. Otherwise `EROFS` — the source cannot
   be removed, so the rename would leave it still visible and amount to
   a copy.
2. The destination must not be provided by a stratum of **higher**
   precedence than `P`. Otherwise `EROFS` — the renamed object would be
   shadowed at its destination and unreadable through the path it was
   renamed to.
3. `P` must hold the directory containing the destination. Otherwise
   `EXDEV`. That directory is not created to satisfy the condition,
   whether or not `P` is the create stratum: parent materialisation
   exists to receive a copy-up, and a rename is not one.
4. Where the source is a directory, the merged directory must contain
   no entries provided by a stratum other than `P`. Otherwise `EXDEV`,
   since those entries cannot move with it. Determining this reads
   every participating stratum, so traverse and list rights are
   required on each, checked before any enumeration begins; where that
   is refused the rename fails with `EACCES` without disclosing whether
   other strata contributed.
5. Where the destination is provided, its type must match the source's.
   A non-directory onto a directory provider fails with `EISDIR`; a
   directory onto anything else fails with `ENOTDIR`. Only the
   provider's type is compared, since a lower stratum's entry of a
   different type is masked and contributes no inode.
6. Where the destination's provider is a directory, that merged
   directory must contain no entries at all — the same merged-emptiness
   test `rmdir` uses, with the same access requirement. Otherwise
   `ENOTEMPTY`.
7. The rename is performed within `P`: both parents are resolved at the
   provider's index, and a single `vfs_rename` is issued there.

Where the destination is provided by a stratum of lower precedence than
`P` and both are non-directories, the rename succeeds and the renamed
object shadows it. Where the destination is held by `P` itself, it is
replaced, as on any filesystem.

Where the renamed object and the destination are both directories, the
result is not a shadowing: by §4.3.2 the renamed directory merges with
the lower strata's directories of that name. Condition 6 is what keeps
that tolerable — those directories are empty, so the merged result is
the renamed directory's own contents.

`P` need not be the create stratum. A rename is performed in whichever
stratum provides the source, provided that stratum accepts
modification. A rename whose source and destination are in different
mounts fails with `EXDEV`, refused by the VFS before stratafs is
consulted, and stratafs additionally refuses one spanning two mounts
inside the provider stratum.

The immutable-provider caveat of §4.5.4 applies to condition 1 as well:
an immutable source yields `EPERM` from the VFS rather than `EROFS`.

## Replacing atomically

A rename onto an existing destination is the operation by which most
software replaces a file safely, and it works through a stratafs mount
for a destination provided by a lower stratum. That case is permitted
by condition 2: the destination is shadowed by the renamed object
rather than removed, so no whiteout is required, and the replacement is
a single `vfs_rename` within one directory pair of one stratum — atomic
on the filesystem holding `P`.

Where the source of such a rename is a temporary file the caller
created in the same directory, §4.5.3 placed it in the create stratum,
which never carries `ro`. Conditions 1 and 3 are then satisfied.

The contrast with the supersede disposition (§4.5.3) is worth noticing:
that spans two strata and is not atomic.

## Flags

Conditions 1 and 4 concern whether the source can be moved at all, and
apply under every flag. Conditions 2, 3, 5 and 6 concern the
destination.

| Flag | Behaviour |
|---|---|
| `RENAME_NOREPLACE` | The destination must not be held by **any** participating stratum, not merely by `P`. Conditions 2, 5 and 6 are not evaluated, since each presupposes a destination that exists; where any stratum holds the destination the rename fails with `EEXIST`. |
| `RENAME_EXCHANGE` | Both names must be provided by the **same** stratum, and that stratum must accept modification; otherwise `EROFS`. Conditions 1 and 4 apply to both names. Conditions 2, 5 and 6 are not evaluated: an exchange swaps two names that both already exist, so neither type matching nor emptiness is required of either, exactly as on any filesystem. Condition 3 is subsumed. Where either name is a directory, no stratum other than the providing one may hold entries under either name; otherwise `EXDEV`. |
| `RENAME_WHITEOUT` | Fails with `EINVAL`, checked before everything else. stratafs has no whiteouts and cannot represent one. |

Exempting `RENAME_EXCHANGE` from conditions 5 and 6 is what leaves the
flag usable. Its ordinary purpose is to swap two populated directories
atomically, which condition 6 would refuse outright and condition 5
would refuse whenever the two differ in type. The stranded-entries
condition is the only destination constraint an exchange genuinely
needs, because it is the only one that arises from the names spanning
strata rather than from what the names hold.

### The `RENAME_NOREPLACE` ordering

A `RENAME_NOREPLACE` whose destination is held by any participating
stratum fails with `EEXIST`, and that `EEXIST` takes precedence over
conditions 1, 3 and 4. It is not stratafs that decides this. For
`RENAME_NOREPLACE` the VFS looks the destination up with `LOOKUP_EXCL`
and returns `EEXIST` for a positive dentry before `vfs_rename` runs at
all, and stratafs's merged lookup makes the dentry positive whenever any
stratum holds the name. `namei.c` is unpatched, so there is no point
inside `->rename` from which the order could be changed.

stratafs nonetheless evaluates conditions 1, 3 and 4 first, and the code
says so. That ordering is reachable only as a race backstop — where the
destination appeared between the VFS lookup and the rename — so a caller
should not expect `EROFS`, `EXDEV` or `EACCES` from a `RENAME_NOREPLACE`
whose destination already existed.

## Other behaviour

Unknown `flags` bits are neither rejected nor masked; they pass through
to the VFS. Where the two provider-level names resolve to one inode the
rename is a no-op returning success. A dentry whose private state is
missing, or whose provider identity no longer matches, yields `ESTALE`.
Because the filesystem sets `FS_RENAME_DOES_D_MOVE`, stratafs performs
the `d_move` or `d_exchange` itself, together with swapping the
dentries' recorded relative paths.

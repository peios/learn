---
title: The Stratum Stack
description: A mount is its stratum stack — an ordered, non-empty list fixed for the mount's life — plus the resolution context and the create stratum.
---

A mount is defined by its stratum stack: an ordered, non-empty list of
strata, highest-precedence first. The stack is fixed for the life of
the mount. Nothing reorders it, and precedence never varies by path, by
caller, or by operation.

Index 0 is the highest-precedence stratum. That convention runs all the
way through: strata are stored in a fixed array in mount-option order,
presence across the stack is a `u64` bitmap indexed by the same
position, and selecting the provider is the trailing-zero count of that
bitmap — the lowest set index, which is the highest-precedence stratum
that holds the name.

The array is `STRATAFS_MAX_STRATA` entries, which is **16**. A stack
longer than that is refused at parse time. Absence never renumbers
anything: an absent stratum simply has its bit clear, keeping its slot
and its precedence.

## A stratum is a path

What is stored for each stratum is a string and a flag word — nothing
else. No reference is held on a stratum's directory, and no resolution
result is retained across operations. Every time a name is resolved,
the stratum's path string is joined with the relative path of the name
and walked from scratch.

This is what makes a stratum follow a wholesale replacement. A package
transaction that renames the old tree aside and the new tree into place
leaves the original directory object intact and referenced by anything
that held it; a stratum defined as that object would go on serving the
replaced tree. Defined as a path, it follows.

The cost is that every lookup does the walk. §4.4.2 covers what that
means in practice, because the implementation does not cache
resolutions at all.

## The resolution context

Stratum paths are joined absolute and walked from a root captured when
the mount was created — the creating process's own filesystem root —
under credentials captured at the same moment. Both are pinned for the
life of the mount and released only when the superblock is freed.

The credential override matters as much as the root. A stratum path is
resolved with the mounter's credentials, not with those of whatever
process later touches the mount, so a caller in a different mount
namespace cannot shift what a stratum denotes, and the paths reported
by the origin attribute (§4.7) always name the same things.

Symbolic links and mounts along a stratum's path are followed as they
stand at the moment of resolution, since the walk is an ordinary
`filename_lookup` with no restricting flags. A mount established inside
a stratum is therefore part of that stratum's tree, and one stratum can
span several filesystems — which §4.4.3 has to account for when
deriving inode numbers.

## What a stratum's filesystem must provide

Nothing beyond ordinary directory and file operations. stratafs probes
no capability at mount time: it checks only that each stratum path
resolves, names a directory, is not a duplicate of another stratum, and
does not push the composed stack past the kernel's maximum stacking
depth. There is no test for a usable directory version value, because
nothing in the implementation would use one.

## Flags

Each stratum carries zero or more flags, declared with it in the mount
options and stored as a bit field.

| Flag | Bit | Meaning |
|---|---|---|
| `create` | `STRATAFS_F_CREATE` | This stratum receives newly created objects and is the destination of copy-up. |
| `ro` | `STRATAFS_F_RO` | stratafs does not modify this stratum. |
| `am` | `STRATAFS_F_AM` | This stratum's directory may be absent. |

The stack-wide rules are decided in Rust, in `stratafs-core`: the stack
must be non-empty, must not exceed 16 strata, must contain no
unrecognised flag bit, must not carry `create` twice, and must not
carry `create` and `ro` on one stratum. The crate distinguishes five
error cases, but the C boundary collapses all of them to `EINVAL`, so
the distinction is not observable to a caller.

### `create`

At most one stratum carries `create`, and a stack may carry none, in
which case `create_index` is `-1` and every creation and every copy-up
is refused with `EROFS`. Modification of an object provided by a
stratum that accepts modification is unaffected, because routing tests
the provider before it consults the create stratum at all (§4.5.1).

`create` does not mean "writable", and it is not the only stratum
stratafs writes to. It designates where objects that do not yet exist
in any stratum are created, and where an object is copied when its
provider will not accept a modification. A stratum carrying neither
`create` nor `ro` is modified in place, and any number of such strata
may sit above the create stratum, below it, or both.

### `ro`

`ro` is a stratafs-level assertion, independent of whether the
stratum's filesystem is itself read-only. It is one of three terms in
the predicate that decides whether a stratum **accepts modification**
of an object it provides:

- the stratum does not carry `ro`;
- the provider's mount is not read-only;
- the provider's inode is not marked immutable.

The predicate takes only the superblock, the stratum index, and the
provider path. It reads no credentials, consults no security
descriptor, and calls into KACS not at all — which is what stops a
caller who has been *refused* write access from provoking a copy-up
(§4.5.1).

Note the third term is specifically the immutable inode flag. A file
that is unwritable by its mode bits is not excluded by this predicate;
the write is routed in place and the underlying filesystem refuses it.

### `am`

Without `am`, a stratum's directory must exist when the mount is
created, and a mount whose stratum directory is absent fails with
`ENOENT`. With `am`, an absent directory is accepted at mount time.

The flag governs mount time only. At runtime the resolver never
consults it: a stratum whose directory has gone is skipped exactly the
same way whether or not it carries `am`. §4.2.4 covers what absence
means once the mount is live.

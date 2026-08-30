---
title: Write Routing
description: Which single stratum a modification is performed against, when that decision is made, and what shared writable mappings do to it.
---

An operation that modifies an existing object is performed against
exactly one stratum. This section covers which, and when the decision
is made.

## Accepting modification

A stratum **accepts modification** of an object it provides when all
three of the following hold:

- the stratum does not carry `ro`;
- the provider's mount is not read-only;
- the provider's inode is not marked immutable. [*write.accepts-modification]

The predicate is a property of the stratum and the object alone. It
takes the superblock, the stratum index and the provider path, and
nothing else — no credentials, no security descriptor, no access
check. [*write.predicate-ignores-caller]

That restriction is load-bearing. Were the predicate to take the
caller's rights into account, a caller *refused* write access by the
provider's descriptor could still provoke a copy-up: the write would
fail, but the copy would have been published, and from then on the
merged path would resolve to a snapshot the provider's legitimate
writer could no longer update. A caller with no write access at all
could freeze any file in the mount.

Note the third term is the immutable inode flag specifically, not
unwritability in general. A file that is unwritable by its mode bits is
routed in place and refused by the underlying filesystem. [*write.unwritable-mode-routes-in-place]

## The rule

The decision itself is `route_existing` in `stratafs-core`, which takes
the provider index, whether it accepts modification, the create index
and whether the create stratum is present, whether the object is of a
copyable type, and whether the stratafs mount itself is read-only. It
returns one of three routes.

1. If the **mount** is read-only, the route is read-only. This term
   short-circuits everything else. [*write.read-only-mount-short-circuits]
2. If the provider accepts modification, the operation is performed
   against the provider's object. [*write.in-place-when-provider-accepts]
3. Otherwise, if the object is copyable, a create stratum exists, is
   present, and has **strictly higher precedence than the provider**,
   the object is copied up and the operation performed against the
   copy. [*write.copy-up-when-create-outranks]
4. Otherwise the route is read-only and the operation fails with
   `EROFS`. [*write.erofs-when-no-writable-stratum]

The strict `create_index < provider` comparison is what stops a
modification being placed where something already present would shadow
it. Where a high-precedence stratum provides a name it will not accept
a write for, there is no lower stratum that can take the write without
the result vanishing behind the provider, so `EROFS` is the honest
answer — reported at the moment of the write rather than discovered
later.

Where the name is held by no stratum, the operation is a creation and
§4.5.3 applies instead.

## When the decision is made

Routing happens when a modifying operation is performed, not when a
descriptor is opened. Every mutating entry point calls
`route_existing` afresh against the provider it currently holds;
nothing caches a route decision, and a descriptor opened before the
predicate changed is not revisited. [*write.routed-per-operation]

| Operation | Routes |
|---|---|
| Writing or appending | Yes [*write.routes.write] |
| Truncating, or any other `setattr` | Yes [*write.routes.setattr] |
| Changing mode, owner, timestamps, or the security descriptor | Yes [*write.routes.metadata] |
| Setting or removing an extended attribute | Yes [*write.routes.xattr] |
| `fallocate` | Yes [*write.routes.fallocate] |
| `splice` into the file | Yes [*write.routes.splice] |
| `copy_file_range` and `remap_file_range` | Yes [*write.routes.copy-range] |
| Establishing a shared writable mapping | Yes [*write.routes.shared-mapping] |
| Reading contents, attributes, or extended attributes | No [*write.routes.read-does-not] |
| Opening, for any access | No [*write.routes.open-does-not] |
| Taking or releasing a lock, or a lease | No [*write.routes.lock-does-not] |

The security descriptor and the system access control list are both
reached as extended attributes, so both route through the `setxattr`
path like any other attribute; there is no descriptor-specific code in
stratafs at all. [*write.descriptor-routes-as-xattr]

An open is not itself a routing trigger. `open` computes a route, but
uses it only to decide the flags of the backing open — a non-in-place
route downgrades the provider open to read-only and strips `O_TRUNC`,
deferring rather than deciding. [*write.open-defers-routing] The one case in which an open acts is
`O_TRUNC` on a regular file: that is a modification, so it routes, and
copies up or fails with `EROFS` there and then. The truncation itself
is applied afterwards by the VFS through `setattr`, which routes again
and lands on the copy. [*write.o-trunc-routes-at-open]

Routing at operation time rather than at open is what makes the rule
implementable. A filesystem cannot see what an open asked for in
access-mask terms — the caller's descriptor is stamped by KACS before
the filesystem's own open method runs, and its mask lives in a private
blob a filesystem cannot reach. Nor does it need to: the access check
has already happened by the time an operation reaches stratafs, so a
modifying operation arriving here is one its caller was entitled to
perform, and routing it is a decision about strata alone.

## Shared writable mappings

Establishing a shared writable mapping routes, even though no bytes
have been written, because stores through such a mapping reach the
object without any further filesystem operation — establishment is the
last point at which routing can occur.

The test is on `VM_SHARED` together with `VM_MAYWRITE`, the "could
become writable" bit rather than the "is writable" bit. A `PROT_READ`
shared mapping taken from a writable descriptor therefore routes,
because it can acquire write access later through `mprotect` with no
filesystem operation in between. A private mapping, and a shared
mapping that cannot acquire write access, do not route. [*write.mmap-routes-on-maywrite] Where routing
yields read-only, the mapping is refused with `EROFS`. [*write.mmap-refused-when-read-only]

## What a copy-up does to an open descriptor

A copy-up performed for one descriptor changes which object provides
the name. That descriptor refers to the copy from then on: it keeps the
inode it was opened against while the inode's backing object becomes
the copy (§4.4.3), and its backing file is replaced. [*write.copying-descriptor-follows-copy]

Every other descriptor already open against the original continues to
refer to the original, and any fresh resolution of the path yields a
new inode standing for the copy. [*write.other-descriptors-keep-original] The pre-copy-up file is not closed —
it is retained so that locks and leases taken before the copy-up keep
working (§4.5.7).

## Special files

A FIFO, socket, or device node is opened and written without the
filesystem object being modified: what is written passes to a pipe, a
socket, or a driver, not to the object's contents. Writing to such an
object therefore does not route, and such an object is never copied up
— every routing site gates on the object being a regular file, and the
copyable flag excludes anything that is not a regular file, directory
or symlink. [*write.special-files-never-copied-up]

Copying up a FIFO would sever it: a reader holding the original and a
writer that arrived after the copy would hold two unrelated pipes. A
device node survives copying only by the accident that the copy names
the same device.

Opens, reads and writes are forwarded to the provider whether or not it
accepts modification, since the write-mode downgrade and the `O_TRUNC`
refusal both apply to regular files only. [*write.special-file-io-forwarded] Operations that modify the
object itself — its mode, its descriptor, its extended attributes — do
route, and where the provider does not accept modification they fail
with `EROFS`, because the copy-up branch cannot apply to an object that
is never copied up. [*write.special-file-metadata-erofs]

## `ioctl`

`ioctl` on a regular file is refused unconditionally with `ENOTTY`, and
its compat form with `ENOIOCTLCMD`. [*write.ioctl-regular-file-refused] Stored-file `ioctl`s can mutate
data and would need command-by-command routing, which is not
implemented; refusing is the conservative stand-in. `ioctl` on a
non-regular file is forwarded to the provider. [*write.ioctl-special-file-forwarded]

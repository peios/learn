---
title: Descriptors on Copy-Up
description: A copy-up carries the source's descriptor rather than inheriting a new one — how it is carried, what failure means, and why preservation wins.
---

Copy-up produces a second instance of an existing object. Its security
descriptor is the source's — owner, group, discretionary list, system
list and integrity label alike — and it is KACS that carries it, not
stratafs.

## How it is carried

When a copy-up context is created, the provider's complete effective
descriptor is resolved and pinned as a byte string on the context. Each
create phase copies those bytes into the phase, and the inode security
initialisation for the created object installs them verbatim instead of
running inheritance. Nothing is reconstructed field by field: it is a
copy of the source bytes, so all five components are preserved together.

The canonical descriptor attribute is deliberately excluded from
stratafs's own extended-attribute replication, precisely so that the
two mechanisms cannot disagree.

The separation inside KACS is clean and explicit. The inode security
initialisation takes the copy-up branch first, and taking it
short-circuits the inheritance builder entirely. Ordinary creation in a
create stratum inherits from its parent (§4.5.3); copy-up preserves.
There is no path on which a copied-up object receives an inherited
descriptor.

Directories materialised in the create stratum to hold a copied-up
object are handled the same way, each carrying the descriptor of the
corresponding **provider** directory — the merged provider of that same
relative path, which is what the pre-check of §4.6.2 evaluated against.

## Failure

Where the source descriptor cannot be replicated, the copy-up fails and
the operation that required it fails. A missing, corrupt, unresolvable,
oversized or unsupported descriptor fails the phase before the
destination is created, and an absent pinned descriptor at install time
fails the create. Nothing publishes a copied-up object carrying any
other descriptor: the descriptor is installed at inode creation, before
any content, and publication is a link or rename of an object already
stamped, so there is no window in which a differently-protected object
is reachable.

The failure errno is not the specified one. §4.8's table pairs
descriptor failure with `EIO` alongside extended-attribute failure, and
the extended-attribute half does report `EIO`. The descriptor half is
carried by KACS, whose failures surface as `EACCES`, `EOPNOTSUPP`,
`EINVAL`, `ESTALE` or `ENOMEM`; there is no `EIO` anywhere on that
path. This is tracked as a defect.

## Why preservation rather than inheritance

Copy-up is reachable by any caller with the right to modify the source
object. That right does not include the right to modify the source's
descriptor, which is a separate right.

Were a copied-up object to receive an inherited descriptor, a caller
holding only write access to a restrictively protected object could
cause a copy of it to exist carrying the create stratum directory's
inheritable entries — and that copy, having higher precedence, would
become what the merged path resolves to. The object's confinement would
have been replaced by the directory's, through an operation the caller
was entitled to perform, without their ever holding the right to alter
a descriptor.

Preserving the source descriptor closes that: a copy is exactly as
reachable as its original, and copy-up changes which stratum holds an
object without changing who may reach it.

## Provenance

Because the descriptor is preserved, the copy's descriptor-level owner
is the owner of the object it was copied from, not the caller who
caused the copy. Ownership therefore does not record who created the
copy and cannot be relied on to; the audit record of §4.6.5 is where
that is available.

Setting the copying caller as the descriptor owner would have preserved
provenance, and was rejected: an owner holds implicit rights over an
object's descriptor, so making the caller the owner would reintroduce
the escalation this section exists to prevent by a slightly longer
route.

The POSIX owner is a different matter, and is *not* preserved — §4.5.8
records what follows.

## What "the source's descriptor" means

The descriptor pinned at the start of a copy-up is the provider's
**effective** descriptor rather than its raw stored attribute. On a
provider mount whose own policy class synthesises, that would be the
synthesised value. In practice that case is unreachable: reaching the
object through the stratafs mount at all requires a real descriptor,
under stratafs's own deny-missing class (§4.6.4). A provider on an
unmanaged mount is refused outright.

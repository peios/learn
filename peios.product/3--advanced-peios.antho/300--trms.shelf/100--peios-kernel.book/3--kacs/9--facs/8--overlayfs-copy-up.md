---
title: Overlayfs Creates
description: Overlayfs performs a create as the mounter, in a directory the caller never named — so KACS resolves the descriptor before the create and hands it down on a credential.
---

Overlayfs is a different problem from the StrataFS context of §3.9.7.
Nothing here needs an authorization exemption: the caller has already
been authorized against the merged inode. What has to be corrected is
the **descriptor** the new object ends up wearing.

Both of the inputs the inheritance algorithm needs (§PCDS 5.6) are
wrong by the time the real create runs:

- **The parent is wrong.** Overlayfs creates on the upper filesystem, in
  the upper directory or — for a copy-up, or a create over a whiteout —
  in the overlay's **workdir**. Neither is the directory the caller
  named. A backing directory is also a distinct inode with its own
  descriptor cache, so a descriptor set at runtime through the overlay
  is not the one a create sees.
- **The subject is wrong.** Overlayfs performs upper-layer work under
  the mounter's credentials. The subject the inheritance algorithm sees
  is therefore the principal that mounted the filesystem, not the one
  making the object.

Left alone, the second is the more damaging: on a live image the root
is an overlay mounted by the system, so every object created anywhere
on it came out owned by SYSTEM, and every inherited `CREATOR OWNER` ACE
resolved to SYSTEM rather than to the principal that created the object.

KACS resolves the descriptor **before** the create, while both inputs
are still right, and hands the answer down. [*facs.ovl-copy-up.resolve-before-create]

## The descriptor rides on a credential [*facs.ovl-copy-up.descriptor-on-credential]

The kernel offers two hooks for this, and both work the same way: they
hand the LSM a credential to fill in, and overlayfs then performs the
creation under it.

| Hook | Fires for | KACS resolves |
|---|---|---|
| `security_inode_copy_up` | A lower object being materialised in the upper layer | The source object's own effective descriptor [*facs.ovl-copy-up.copy-up-hook-resolves-source] |
| `security_dentry_create_files_as` | An ordinary create, mkdir, mknod, symlink or tmpfile | Inheritance from the overlay parent, for the calling principal [*facs.ovl-copy-up.create-hook-resolves-inheritance] |

Either way the result is attached to that credential, and the inode
creation path prefers it over computing inheritance itself. [*facs.ovl-copy-up.creation-prefers-attached]

The credential is what makes the lifetime sound, and it is the reason
this needs no context of its own:

- Overlayfs installs the credential with `override_creds()` and reverts
  it through a scope guard, on every exit path including errors. [*facs.ovl-copy-up.credential-reverted-on-every-path]
- Each scope wraps exactly one creation and nothing else. [*facs.ovl-copy-up.one-creation-per-scope] A create over
  a whiteout makes one temporary object and then *renames* it over the
  whiteout, rather than creating a second.
- Releasing the credential releases the descriptor. [*facs.ovl-copy-up.release-frees-descriptor]

So there is nothing to arm and nothing to disarm. Outside that scope the
credential is simply not current.

A credential *derived* from one carrying a pending descriptor does not
inherit it. [*facs.ovl-copy-up.derived-credential-does-not-inherit] Without that rule the descriptor would escape its create and
be stamped on the next unrelated object the task made.

## A copied-up object keeps its own descriptor [*facs.ovl-copy-up.copy-up-preserves-descriptor]

A copy-up is not a new object, and inheritance is the wrong answer for
it even from the right parent: the object already had a descriptor.
KACS carries the source's across, whether that descriptor was stored on
the lower inode or synthesized for it under a mount policy (§3.9.5). [*facs.ovl-copy-up.source-descriptor-may-be-synthesised]

Without this the defect runs in both directions. An object with a
deliberately narrow descriptor is widened by the act of writing to it,
and a deliberately permissive one is narrowed — in both cases changing
what *other* principals may do to it as a side effect of somebody
else's write. The principal doing the writing already held write access;
nothing about that should re-decide the object's policy for everyone
else.

## An ordinary create inherits from the overlay [*facs.ovl-copy-up.create-inherits-from-overlay]

A genuinely new object has nothing to preserve, so it inherits — but
from the merged directory the caller named and as the caller, which is
what it would have got had overlayfs not been in the way. The parent's
descriptor is read through the overlay inode, so a descriptor set at
runtime governs the children created after it, and `CREATOR OWNER`
resolves to the principal making the object. [*facs.ovl-copy-up.creator-owner-resolves-to-caller]

A creator descriptor supplied explicitly to a native create (§3.9.2) is
picked up here for the same reason. [*facs.ovl-copy-up.supplied-descriptor-honoured] The request records the parent the
caller resolved — an overlay inode — so a match attempted at inode
creation time, where only the backing inode is visible, could never
fire, and the descriptor the caller asked for would be silently replaced
by inheritance.

A caller with no token is left alone rather than denied here, so the
inode creation path reaches its own denial. [*facs.ovl-copy-up.no-token-passes-through] Two places must not decide
the same thing differently.

## The descriptor xattr is not copied [*facs.ovl-copy-up.canonical-xattr-discarded]

On copy-up the canonical descriptor xattr is discarded during the xattr
copy rather than replicated, because the credential above already
carries it; copying it as well would overwrite the descriptor with the
same answer. It could not be copied through that path in any case — the
canonical xattr is not readable or writable as an ordinary xattr, since
descriptor mutation is the dedicated interface's job (§3.9.6).

## Failure [*facs.ovl-copy-up.resolve-failure-fails-create]

Failing to resolve a descriptor fails the create. That holds for both
hooks: a source whose descriptor cannot be read fails the copy-up, and a
parent whose descriptor cannot be resolved — or which does not grant the
caller the right to add the object — fails the create.

The alternative in each case is to fall back to inheritance from a
backing directory as the mounter, which is the outcome this exists to
prevent, and which leaves nothing behind to find later.

An object on an unmanaged mount is the one case that passes through
untouched: there is nothing there to preserve or to inherit. [*facs.ovl-copy-up.unmanaged-untouched]

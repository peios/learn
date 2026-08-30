---
title: Overlayfs Copy-Up
description: A file copied up keeps its own security descriptor rather than inheriting one — where the descriptor is carried, and why the cred is the right place for it.
---

Overlayfs copy-up is a different problem from the StrataFS context of
§9.7. Nothing here needs an authorization exemption: the caller has
already been authorized against the merged inode, and overlayfs performs
the copy under its own credentials. What has to be preserved is the
**descriptor**.

## The object keeps its own descriptor

When overlayfs materialises a lower object in the upper layer, it
creates a new inode, and a newly created inode ordinarily takes its
descriptor from inheritance. That is the wrong answer here, and not
only because the object already had one: the directory it is created in
is the overlay's **workdir**, not the destination parent, so the
inherited descriptor does not even correspond to where the object
finally lands.

KACS therefore carries the source's descriptor across. A copied-up
object keeps the descriptor it had, whether that descriptor was stored
on the lower inode or synthesized for it under a mount policy (§9.5).

Without this the defect runs in both directions. An object with a
deliberately narrow descriptor is widened by the act of writing to it,
and a deliberately permissive one is narrowed — in both cases changing
what *other* principals may do to it as a side effect of somebody
else's write. The principal doing the writing already held write access;
nothing about that should re-decide the object's policy for everyone
else.

## The descriptor rides on a cred

`security_inode_copy_up` does not merely notify an LSM that a copy-up is
starting. It offers the LSM a credential to fill in, and overlayfs then
performs the creation under it. KACS captures the source's effective
descriptor there and attaches it to that credential; the inode creation
path prefers it over computing inheritance.

The credential is what makes the lifetime sound, and it is the reason
this needs no context of its own:

- Overlayfs installs the credential with `override_creds()` and reverts
  it through a scope guard, on every exit path including errors.
- The scope wraps exactly one creation and nothing else.
- The hook runs once per copied-up object, so an intermediate directory
  carries its own descriptor rather than the descriptor of the file whose
  copy-up caused it to be created.
- Releasing the credential releases the descriptor.

So there is nothing to arm and nothing to disarm. Outside that scope the
credential is simply not current.

A credential *derived* from one carrying a pending descriptor does not
inherit it. Without that rule the descriptor would escape its copy-up
and be stamped on the next unrelated object the task created — an object
wearing a descriptor lifted from a file it has nothing to do with.

## The descriptor xattr is not copied

The canonical descriptor xattr is discarded during the xattr copy rather
than replicated, because the credential above already carries it;
copying it as well would overwrite the descriptor with the same answer.
It could not be copied through that path in any case — the canonical
xattr is not readable or writable as an ordinary xattr, since descriptor
mutation is the dedicated interface's job (§9.6).

## Failure

A source whose descriptor cannot be read fails the copy-up. The
alternative is to fall back to inheritance, which is the outcome this
exists to prevent, and which leaves nothing behind to find later.

An object on an unmanaged mount is the one case that passes through
untouched: it has no descriptor to preserve.

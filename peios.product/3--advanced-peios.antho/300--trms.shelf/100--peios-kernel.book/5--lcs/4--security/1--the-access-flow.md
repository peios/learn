---
title: The Access Flow
description: The registry's security model is KACS applied to keys — no traverse checking, symlink handling, and why an fd is a capability.
---

The registry's security model is KACS applied to keys. LCS defines no
access control mechanism of its own: the same AccessCheck, the same
Security Descriptors, the same tokens and SIDs that every other Peios
subsystem uses. What this section describes is how those primitives
attach to registry operations.

Every open follows the same five steps.

1. **Token capture.** LCS takes the calling thread's effective token —
   the impersonation token if one is set, otherwise the process primary
   token. This is the same capture KACS performs for every syscall.

2. **Path resolution.** LCS walks the path through the layer stack,
   following symlinks. **No access check happens during the walk.**
   Intermediate keys are not evaluated; only the final key matters.

3. **AccessCheck.** LCS calls KACS AccessCheck with the captured token,
   the final key's Security Descriptor as returned by the source, and
   the desired access mask. Every requested right must be granted or
   the open fails with `EACCES`. There is no partial grant: the caller
   gets what it asked for or nothing.

   `MAXIMUM_ALLOWED` is the exception, and the only way to ask for
   whatever is available. AccessCheck computes the full allowed set and
   that becomes the granted mask.

4. **The granted mask is stored on the fd.** It never changes.

5. **Per-ioctl checks are bitmask tests.** Each ioctl has a required
   right; LCS tests the fd's granted mask against it and returns
   `EACCES` without contacting the source if it is absent. The
   Security Descriptor is not re-read and AccessCheck is not
   re-evaluated.

## No traverse checking

LCS checks nothing on the way down. A process can open
`Machine\System\Services\Jellyfin` without holding any access to
`Machine\System\Services` or `Machine\System`.

This matches the Windows registry and is a deliberate difference from
filesystem path semantics, where every directory in a path is checked
for traverse. It means a key's Security Descriptor is the whole story
about who can reach it, and that an ancestor's descriptor confers no
protection on its descendants.

## Symlinks

Opening a symlink follows it, and AccessCheck runs on the **target**
key, not the link. `REG_OPEN_LINK` opens the link itself instead — but
only for the final path component. A symlink encountered part-way
through a path is followed regardless.

Creating a symlink is privileged: `KEY_CREATE_SUB_KEY` and
`KEY_CREATE_LINK` on the parent, plus either `SeTcbPrivilege` or
membership of Administrators (§5.2.4).

## Fds are capabilities

A key fd can be passed over a Unix socket with `SCM_RIGHTS`, and it
carries its granted mask with it. The recipient gets the access the
original opener was granted, whether or not its own token would have
passed AccessCheck.

This is explicit delegation and it is consistent with how fds work
everywhere else in Peios. Passing a `KEY_WRITE` fd hands over write
access.

Opening relative to a parent fd skips path parsing and AccessCheck for
the parent portion — the caller already proved its access when it
obtained the parent fd. This is the ordinary way to traverse a subtree.

## Changing a descriptor does not revoke a handle

A Security Descriptor change takes effect for future opens. An fd that
already exists keeps the mask it was granted at open, because that is
what semantic rule 5 says (§5.1). The recourse for genuinely revoking
access is to restart the process holding the fd.

Descriptor changes are also not layer-qualified. They are direct
mutations on the key object, and deleting a layer does not undo one
(§5.1, rule 4).

## The second check nobody expects

Every layer-qualified mutation runs a **second** AccessCheck, against a
different object: the metadata key of the layer being written to. That
check is for `KEY_SET_VALUE` and it is in addition to the fd's granted
mask on the target key. Both must pass. §5.3.4 covers it.

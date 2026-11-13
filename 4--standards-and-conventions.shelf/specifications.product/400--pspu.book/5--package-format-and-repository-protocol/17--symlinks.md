---
title: Symbolic Links
description: Symbolic links as entries of their own, their targets, links that cross into other packages, and why a link has no security descriptor.
---

A symbolic link is an entry of its own (§5.16): it is never followed when a
package is packed or composed.

## Targets

A link's target is recorded exactly as `readlink` returns it, and MUST be
valid UTF-8. A relative target resolves from the link's own directory. An
absolute target resolves from the root of the system, not from `/usr`, where
the package's own paths are: a package's `bin/sh` linking to `dash`
resolves to `/usr/bin/dash`, and one linking to `/usr/bin/dash` does too.

## Across packages

A link MAY point into another package, or at nothing. The format doesn't
check that a target exists, since what is there depends on the closure the
link is composed into.

## Integrity

A link's target is part of its entry, so the manifest's identity covers it.

## No descriptor

A link has no security descriptor of its own: access to what it reaches is
the target's. A link MUST NOT be given one (§5.20). A link created when a
closure is built takes what its directory gives it.

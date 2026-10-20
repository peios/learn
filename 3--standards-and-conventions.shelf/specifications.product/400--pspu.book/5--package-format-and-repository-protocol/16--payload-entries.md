---
title: Payload Entries
description: Tar permission bits are distribution metadata and establish no access control — plus empty directories, path ownership, and forward compatibility.
---

## Permissions

Tar entry permission bits in a package are distribution-format metadata
only. They establish no access control on the installed file. Access
control is the consumer's responsibility: on Peios, through a security
descriptor applied at file-creation time (§5.20); on any other system
extracting a package for inspection or migration, through that system's
native mechanism applied after extraction.

Every payload entry's permission bits MUST be `0777`. Any other value
MUST cause the package to be rejected.

The setuid and setgid bits MUST NOT be set on a payload entry.
Privilege escalation on Peios is mediated by the kernel's access-control
subsystem, not by filesystem-level setuid; a setuid bit is meaningless
to the access-check path and MUST NOT appear in installed content.

> [!NOTE]
> The `0777` rule is honest signalling. A `0644` or `0755` mode would
> imply a permission contract the format does not enforce and the kernel
> does not consult. Fixing every entry to `0777`, combined with the
> uid/gid and owner/group rules of §5.11, treats a payload as
> identity-free, permission-free transport bytes.
>
> One consequence: extracting a package with a generic tar tool on a
> non-Peios host produces world-writable files. This is intended.
> Tooling that needs sensible host-native permissions on extracted files
> is responsible for applying them after extraction.

## Empty directories

A package MAY install an empty directory: a tar entry of type directory
with no content. Empty directories establish paths a runtime will need,
and are the only content permitted under `/var/` (§5.14).

## One package per path

Two packages MUST NOT install a file at the same install path. A
consumer MUST detect the collision and reject the second install.

A package MAY install content into a directory another package created;
directory creation is idempotent. The rule applies to non-directory
entries only.

The one exception is a claim link (§5.23), which belongs to the consumer
rather than to any package and is materialised only at a path no
installed package owns.

## Detached signatures

A payload entry whose path ends in `.peios.sig` is a **detached
signature**: the 3310-byte binary-signature blob of PSPK chapter 3 for
the entry whose path is the same with that suffix removed (its
**target**), stored as ordinary payload bytes. The suffix is reserved;
a package MUST NOT use it for any other purpose.

This is how a signature reaches a file that cannot carry one in an ELF
section. §5.11 forbids extended attributes on tar entries, so the
`security.peios.sig` placement PSPK defines cannot travel inside a
package; the detached entry carries the same blob as payload instead,
and the consumer derives the attribute from it.

A consumer MUST reject a package in which a detached signature:

1. has no target — the path without the suffix is not a payload entry
   of the same package, or is a directory or symlink entry;
2. is not exactly 3310 bytes, or its first byte is not `0x01`; or
3. has a target whose first four bytes are `\x7fELF`. An ELF file
   carries its signature in its `.peios.sig` section; giving it a
   detached signature as well would leave two carriers for one file,
   and PSPK's lookup order would silently ignore the second.

A consumer that installs the target MUST, as part of creating the file
and before the file becomes visible at its install path, set the
extended attribute `security.peios.sig` on it to exactly the detached
entry's bytes, and MUST NOT create a file at the detached entry's own
path. The detached entry is transport for the attribute, not content:
it is not installed, is not recorded as a file the package owns, and
takes no part in the one-package-per-path rule above. Removing or
replacing the target removes or replaces the attribute with it.

The consumer verifies nothing about the signature beyond its shape. The
blob is the signer's assertion and the kernel's to verify; a consumer
that can install the package cannot generally hold the keys that would
let it check the blob, and MUST NOT refuse a package because it cannot.

> [!NOTE]
> A consumer extracting a package on a system where the attribute
> cannot be set — an unprivileged inspection, a filesystem without
> `security.*` support — has produced a root in which those files are
> unsigned, exactly as if a copy had dropped the attribute. That is the
> fail-closed outcome the kernel's verifier is designed for, but such a
> consumer SHOULD report it rather than proceed silently.

## Forward compatibility

The triplet path convention of §5.15 is designed so that a future
multi-architecture system MAY install foreign-architecture packages
alongside native ones without filesystem-level collisions.

In this version only one architecture's packages may be installed on a
given system at a time (§5.8). The triplet convention applies
regardless, so that a package conforming to this version stays
forward-compatible with such an extension.

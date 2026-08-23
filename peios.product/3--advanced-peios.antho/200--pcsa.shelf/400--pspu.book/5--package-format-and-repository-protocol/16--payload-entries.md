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

## Forward compatibility

The triplet path convention of §5.15 is designed so that a future
multi-architecture system MAY install foreign-architecture packages
alongside native ones without filesystem-level collisions.

In this version only one architecture's packages may be installed on a
given system at a time (§5.8). The triplet convention applies
regardless, so that a package conforming to this version stays
forward-compatible with such an extension.

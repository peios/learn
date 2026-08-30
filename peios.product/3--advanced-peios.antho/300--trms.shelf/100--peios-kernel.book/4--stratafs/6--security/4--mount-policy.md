---
title: Mount Policy
description: Every stratafs mount carries the FACS policy class that denies access to an object with no readable descriptor, and what follows from that.
---

A stratafs mount carries the FACS mount policy class that denies access
to an object with no readable security descriptor. The class is derived
from the filesystem magic, not from an administrative choice: the
policy resolver maps the stratafs magic to the deny-missing class, and
falls back to that mapping whenever a cached policy value is not one of
the valid ones. [*security.mount-policy-is-deny-missing]

It cannot be set to anything else. The set path rejects a superblock
carrying the stratafs magic with `EOPNOTSUPP` **before** it validates
its arguments or checks privilege, and there is no mount option to
choose one — stratafs's parameter table holds exactly one entry, and
anything else is refused. [*security.mount-policy-cannot-be-set] Reading a mount's policy is itself privileged,
requiring TCB privilege, though for stratafs the answer is fixed. [*security.mount-policy-read-requires-tcb]

Two classes are excluded for distinct reasons.

**The unmanaged class** declares that FACS does not apply to a mount and
that the kernel governs it by rules particular to that filesystem.
stratafs has no such rules: it delegates every decision to the provider
(§4.6.1). An unmanaged stratafs mount would therefore have no access
control at all — not delegated control, but none — for every object
reachable through it. That is not theoretical: enforcement points
consult the mount policy of the superblock an object belongs to before
performing their check, and treat an unmanaged mount as requiring none.
For a mount established over a directory of executables, that would
place every program on the system beyond the execute check.

**The synthesising classes** would have stratafs supply a descriptor of
its own for an object whose provider has none. Either consequence is
disqualifying: the mount would grant access to an object that is
unreachable through its own stratum, falsifying the guarantee the whole
of §4.6 rests on; and the class that persists a synthesised descriptor
would write it back onto the provider's object, which stratafs may not
do to any stratum and certainly not to one carrying `ro`.

## Missing descriptors

Where a provider object has no descriptor, access through the stratafs
mount is denied under the mount's own policy, and the provider
filesystem's policy is not consulted. Both paths implement this:
stratafs's own merged-directory check turns `ENODATA` or `EOPNOTSUPP`
straight into `EACCES` rather than asking the provider's superblock to
synthesise, and an object open resolves the missing-descriptor policy
against the **stratafs** superblock, yielding a missing-descriptor
cache entry and then `EACCES`. [*security.missing-descriptor-denied]

A descriptor that is present but cannot be interpreted is a distinct
case and is not routed to mount policy. It takes the ordinary
corrupt-descriptor outcome: a corrupt cache entry and an emitted event
on the open path, and a validation failure on the merged-directory
path. The two produce the same errno by different routes, and mount
policy is consulted in neither. [*security.corrupt-descriptor-not-mount-policy]

## Consequence

A stratafs mount is uniform in the sense a mount policy requires: every
object reached through it is subject to the same policy, which is the
mount's own. What varies between objects is the descriptor evaluated,
which is a property of the object rather than of the policy.

Because the policy denies where a descriptor is absent, the divergence
from direct access is always in the refusing direction. An object with
no descriptor on a stratum whose own filesystem would synthesise one is
refused through the stratafs mount while remaining reachable through
its stratum path. An object reachable through its stratum path is never
made *more* reachable by being merged. [*security.merge-never-widens-access] The same holds for a stratum on
an unmanaged filesystem, whose objects carry no descriptors at all:
merging one is permitted but yields nothing readable, and is not a
useful arrangement. [*security.unmanaged-stratum-yields-nothing-readable]

---
title: Pre-Existing Files
description: A path that already exists without belonging to any package — what peipkg does about it, and what it is meant to do.
---

A path may already exist on the filesystem without belonging to any
installed package — left by a manual copy, inherited from a non-Peios
installation, or written by something outside the package manager.

## What peipkg does

peipkg checks whether something exists at the install path. If it does,
the existing entry is renamed aside as a backup and the staged file is
renamed into place. If it does not, the staged file is renamed in.

The check is on existence alone. Ownership is not consulted, the
existing content is not compared against what is about to be installed,
and the operator is not asked.

The backup is discarded when the transaction commits, along with every
other backup (§8.2), so the displaced content does not survive the
operation.

## The intended behaviour

PSPU §5 leaves the handling of an unowned pre-existing file to the
consumer, but the shape peipkg is designed for is three-way:

- **Adopt** it when its content is byte-identical to what would be
  installed. Recording the path as owned without rewriting it is safe,
  because the disk already holds exactly the intended bytes.
- **Fail** otherwise, naming the file, rather than overwriting something
  nobody claimed.
- **Displace** it when the operator explicitly authorises the overwrite,
  keeping the backup rather than destroying it.

None of the three is implemented. What happens today is the middle case
without the failure: overwrite, then discard the evidence.

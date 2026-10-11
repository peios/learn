---
title: Disk Manager
type: how-to
description: Inspect disk identity, partitions, live mounts and startup entries in Disk Manager, and understand its current inspection-only limits.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/partitioning
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
---

Open the launcher and type `disk` to inspect this machine's storage. Select a
disk to check its identity and partitions, **Mounts** to inspect current mounts,
or **At Startup** to review startup entries.

> [!IMPORTANT]
> Disk Manager is currently inspection-only. Its partition, format, mount and
> other change forms run checks but end with a status message saying nothing
> changed. The privileged disk service has not been built. Use
> [`part`](~peios/disks-and-filesystems/partitioning),
> [`mke2fs`](~peios/disks-and-filesystems/mke2fs) and
> [`mount`](~peios/mount-policies/mount) for supported command-line operations.

Before moving to a destructive command, compare the disk's device, model,
serial, exact size, partition layout and mount points. **Not Readable** and
**Contents unknown** are visibility limits; neither means the disk is empty.

## A disk

The disk page shows its model or virtual connection, size and device, with a
**GPT**, **MBR** or **System** indicator. **System** identifies storage Peios is
running from.

Use the bar or the list below it to inspect each partition. The bar is
proportional to size: Linux/ext4 is blue, FAT orange, swap violet, and
unformatted partitions grey. Striped areas are free space. Selecting a
partition opens its page; selecting free space opens the add-partition form.
The list also shows where filesystems are mounted.

**This Disk** gives the device, model, serial, connection, exact size, sector
size and partition table. Removable disks have an **Eject** control. **Erase
Disk** describes creating a new empty GPT and asks for confirmation, but this
and all other change controls still end without changing storage.

## A partition

Check the three groups before choosing a command-line operation:

- **Filesystem:** type, label, UUID, space usage and the **Format** form.
- **Mounts:** mount points, missing-descriptor policy, and **Mount** or
  **Mount Elsewhere**.
- **Partition:** number, type, name, unique ID, start, exact size and **Delete**.

A mounted partition cannot be formatted or deleted until unmounted. Storage
Peios is running from cannot be changed while it runs. Unavailable actions
show why; those checks do not make currently unimplemented changes available.

The **Format** form describes ext4 or FAT32 with a label. For ext4, its initial
root permissions give SYSTEM and Administrators full control, everyone read
access, and creators ownership of objects they create, matching the installer.
Review that policy rather than assuming it matches the administrator-only
`mke2fs` example.

The **Mount** form describes a folder, read-only choice, missing-permissions
policy and whether to mount again at startup. Submitting it currently changes
none of these.

## Files without permissions

The UI labels map to [mount policy classes](~peios/mount-policies/policy-classes):

| In Disk Manager | Policy | Meaning for a missing SD |
|---|---|---|
| Deny Access | `deny-missing` | SD-based access is denied until a valid descriptor is supplied. |
| Give Permissions, Not Saved | `synth-ephemeral` | Derive from parent/template and keep it in memory. No SD is written to the disk. |
| Give Permissions and Save Them | `synth-persist` | Derive an SD and schedule it to be saved. |
| Not Managed | `unmanaged` | FACS does not check this filesystem; the kernel's own per-operation checks still apply. |

A file brought from another system may lack a descriptor, and FAT has nowhere
to store one. Filesystems without SD storage are not offered the persistent
choice. A mount's **Permissions…** view shows the synthesis template used when
its parent supplies none. StrataFS's policy and kernel-reserved unmanaged
policies are fixed.

An ephemeral descriptor can remain cached while the inode is in memory; the
UI's “each time it is opened” description should not be read as a promise of
re-synthesis on every warm open. Corrupt stored descriptors are denied even
with a synthesis policy.

## Mounts

**Mounts** groups filesystems on disks, shared folders, the system's root and
StrataFS views, and the kernel's own filesystems. Select a mount for options and
policy. StrataFS pages also list strata in highest-precedence-first order.

If a later mount covers this mount at the same point or above it, the page says
so. Check this when a mounted filesystem seems to have disappeared from a path.

## At Startup

**Added Here** lists filesystems configured for startup, located by UUID so
they can be found after moving to another port. **Mounted by Peios** shows
system-managed startup mounts and cannot be changed here. The UI does not yet
save changes to either list.

## What you may see and change

Disk changes are described as requiring the Manage Volumes privilege, held by
Administrators. Other users get an inspection view with the limitation
explained once and no change controls. No user can currently commit changes
through Disk Manager because its service is missing.

As shipped, opening a disk to read its table and filesystems is limited to
SYSTEM and Administrators. Other users still see kernel-listed partitions and
mounted types from the mount table. Unavailable details are **Not Readable**
or **Contents unknown**, never “not formatted”.

The Disk Manager guide describes policy reads as requiring Manage Volumes.
Some command/SDK pages instead say TCB only; see the unresolved
[privilege discrepancy](~peios/mount-policies/managing-mounts#check-policy-access)
before diagnosing a policy-read failure.

Disk insertion/removal and mounts changed elsewhere should appear within a
couple of seconds. After a command-line change, inspect the refreshed device,
partition and mount state rather than treating a completed form as success.

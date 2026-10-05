---
title: Disk Manager
type: how-to
description: See this machine's disks, partitions, filesystems and mounts on the desktop with Disk Manager — the partition bar, what each mount does with files that have no permissions of their own, what is mounted at startup, and what you may see and change.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/partitioning
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
---

**Disk Manager** is the desktop's window on this machine's storage. Open
it from the launcher (type `disk`). Down the side are the disks, then
**Mounts** and **At Startup**.

> [!NOTE]
> Disk Manager shows everything today, but it can't change anything yet.
> Partitioning, formatting and mounting are made by a privileged disk
> service, which hasn't been built. Every change has its form and its
> checks, and ends by saying on the status line that nothing was changed.
> Until the service exists, use [`part`](~peios/disks-and-filesystems/partitioning),
> [`mke2fs`](~peios/disks-and-filesystems/mke2fs) and `mount`.

## A disk

Each disk has a page: its model (or how it is connected, for a virtual
disk without one), its size and its device. Beside it is its partition
table, **GPT** or **MBR**, or **System** when Peios runs from it.

Under that, a bar draws the disk from start to end. Each partition is as
wide as its share, in the colour of what it holds:

- blue for a Linux filesystem (ext4);
- orange for FAT;
- violet for swap;
- grey for a partition that isn't formatted.

Free space is striped. Press a partition to open it, or free space to
add a partition there.

The list under the bar says the same in words, in order, with where each
filesystem is mounted. **This Disk** gives the disk's facts: its device,
model, serial number, connection, exact size, sector size and partition
table. **Eject** is there for a removable disk. **Erase Disk** gives the disk
a new, empty GPT table, and asks first.

## A partition

A partition's page has three groups:

- **Filesystem:** its type, label and UUID, how full it is, and
  **Format**.
- **Mounts:** where it is mounted, how files without permissions of their
  own are treated there, and **Mount** (or **Mount Elsewhere**).
- **Partition:** its number, type, name, unique ID, where it starts, its
  exact size, and **Delete**.

What can't be done now says why instead. A mounted partition can't be
formatted or deleted until it is unmounted, and nothing Peios runs from
can be changed while it runs.

- **Format** makes ext4 or FAT32, with a label. For ext4 it also sets the
  permissions of the new filesystem's top folder. As it starts, SYSTEM
  and Administrators have full control, everyone may read, and whoever
  makes something inside owns it: the same as the installer gives the
  disk it installs to.
- **Mount** chooses:
  - the folder;
  - whether it is read-only;
  - what happens to files with no permissions of their own;
  - whether it is mounted again at every startup.

## Files without permissions

Every mount has a [mount policy](~peios/mount-policies/policy-classes):
what Peios does with a file that has no permissions of its own. A file
copied on from another system has none, and FAT can't store any. Disk
Manager names the policies by what they do:

| In Disk Manager | Policy | Means |
|---|---|---|
| Deny Access | `deny-missing` | Nobody can open the file until it is given permissions. |
| Give Permissions, Not Saved | `synth-ephemeral` | The file is given its folder's permissions, or the mount's template, each time it is opened. Nothing is written to the disk. |
| Give Permissions and Save Them | `synth-persist` | The same, but the permissions are written to the file, once. |
| Not Managed | `unmanaged` | The kernel doesn't check permissions on this filesystem. |

A filesystem that can't store permissions, such as FAT, isn't offered the
one that saves them. A mount's page shows its policy, and **Permissions…**
shows the template that files are given where their folder has none to
pass on. A StrataFS view's policy is fixed, and so is a filesystem's the
kernel doesn't manage.

## Mounts

**Mounts** lists everything mounted, in four groups:

- filesystems on disks;
- shared folders;
- the system (its root and its StrataFS views);
- the kernel's own filesystems.

A mount that a later one covers, at the same place or above it, says so.
Its page gives its options and its policy. For a StrataFS view it also
gives the strata, top first.

## At Startup

**Added Here** lists the filesystems mounted every time this machine
starts. Each one is found by its UUID, so it is found again wherever it is
plugged in. **Mounted by Peios** lists what Peios mounts itself as it
starts, which isn't changed here.

## What you may see and change

Changing disks needs the Manage Volumes privilege, which Administrators
hold. Anyone else sees everything there is to see, with the reason said
once, and nothing to press.

What there is to see also depends on who you are. Opening a disk to read
its partition table and filesystems is, as shipped, for SYSTEM and
Administrators only. For anyone else:

- a disk's partitions are still shown, as the kernel lists them;
- a mounted filesystem's type comes from the mount table;
- everything else is marked **Not Readable** or **Contents unknown**,
  never "not formatted".

A mount's policy can only be read with Manage Volumes too.

Disk Manager notices a disk plugged in or taken out, and anything mounted
or unmounted elsewhere, within a couple of seconds.

---
title: Stable device names
type: concept
description: "Why /dev/vda is not a name to keep, what /dev/disk/by-uuid and its siblings are, who creates them, and where they are not available."
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/partitioning
  - peios/disks-and-filesystems/installing-to-disk
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/services-and-jobs/boot-and-boot-modes
---

The kernel names a disk by the order it found it in: `/dev/vda`, `/dev/sda`, `/dev/nvme0n1`. That order is whatever the hardware produced this time — a second controller that probed faster, a USB stick that was plugged in, a disk that moved to another port — so the same disk is not guaranteed the same name on the next boot. A name of that kind is fine for a command you type now and wrong for anything written down: a boot cmdline, a mount reference, a script.

Peios keeps kernel names for the moment and gives every disk a set of **stable names** for everything else. They live under `/dev/disk/`, as symlinks to whatever kernel name the device happens to have:

| Directory | Keyed by | Example |
|---|---|---|
| `by-uuid` | the filesystem's UUID, written when it was formatted | `4ED7-A6AC -> ../../vda2` |
| `by-label` | the filesystem's label | `PEIOS -> ../../vda` |
| `by-partuuid` | the GPT partition entry's UUID | `2036ae68-…-f118299d5446 -> ../../vda2` |
| `by-partlabel` | the GPT partition entry's name | |
| `by-id` | the hardware's own identity: model and serial, or WWN | `nvme-QEMU_NVMe_Ctrl_peiosnvme1 -> ../../nvme0n1` |
| `by-path` | the bus position the device sits at | |
| `by-diskseq` | the kernel's monotonic disk sequence number, for this boot only | |

Which one to use depends on what you mean. A *filesystem* is `by-uuid` — it follows the data if the disk is cloned, and it is what `root=UUID=` on the kernel command line names. A *partition* independent of what is on it is `by-partuuid`. A *physical disk* whatever is written to it is `by-id`. `by-label` is the human-friendly one and the only one that is not unique by construction.

Partitions appear under the same keys with the parent's identity plus `-partN`, so `by-id/nvme-…-part2` is the second partition of that NVMe disk.

## Who creates them

The names are made by the **device manager**, eudev, which peinit starts first in phase 2 of boot. As each block device appears — at boot, when it replays the kernel's enumeration, and afterwards whenever a device is plugged in — the device manager probes it (its partition table, and the filesystem signature on each partition) and creates the matching links. Unplug the device and the links go away.

That is the same daemon that loads a driver for each device the kernel reports, so a disk behind a modular controller gets its driver, its kernel name and its stable names from one pass. See [Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes) for where the service sits in the boot order; a service that opens a device by stable name should `Requires` it, because peinit does not release eudev's dependents until the boot-time replay has finished.

The device manager does not decide who may open a device. That is the security descriptor on the node, seeded on `/dev` before any of this runs — see [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

## Where they are not available

**The initramfs has none of them.** No device manager runs there — only a single pass that loads drivers, described in [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage). The initramfs still honours `root=UUID=`, but it resolves the UUID by probing each block device directly rather than by looking in `/dev/disk/by-uuid`, and `lsblk` does the same. That is why the installer's cmdline works on a machine the initramfs has never seen: it never depended on the links.

**`by-diskseq` does not survive a reboot.** The sequence number is assigned in the order devices appear during *this* boot, which is precisely the property the other directories exist to avoid depending on. It is there for tools that need to tell a re-plugged device from the one it replaced.

## Where to go next

For writing a partition table that gives every partition a `by-partuuid` name, read [Partitioning](~peios/disks-and-filesystems/partitioning).

For how the installer records the root filesystem's UUID into the kernel command line, read [Installing to disk](~peios/disks-and-filesystems/installing-to-disk).

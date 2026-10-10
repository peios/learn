---
title: Stable device names
type: how-to
description: Choose a stable filesystem, partition or disk identity and verify its target before saving a mount reference or changing storage.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/partitioning
  - peios/disks-and-filesystems/installing-to-disk
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/services-and-jobs/boot-and-boot-modes
---

Use a stable identity for a boot command line, saved mount reference or script.
Use the current kernel device name only after checking which device it names
in this boot: `/dev/vda`, `/dev/sda` and `/dev/nvme0n1` depend on discovery order
and can change when hardware, controllers or probe timing changes.

1. Inspect disks and partitions with `part list` and
   [`lsblk`](~peios/mount-policies/lsblk).
2. Choose the identity that matches the object you mean: filesystem UUID,
   partition UUID or hardware identity.
3. Match that identity back to the size, layout and current mounts before any
   destructive operation. A readable link identifies a device; it does not
   establish that its contents can be erased.

The links live under `/dev/disk/` and point to the current kernel name:

| Directory | Keyed by | Example |
|---|---|---|
| `by-uuid` | the filesystem's UUID, written when it was formatted | `4ED7-A6AC -> ../../vda2` |
| `by-label` | the filesystem's label | `PEIOS -> ../../vda` |
| `by-partuuid` | the GPT partition entry's UUID | `2036ae68-…-f118299d5446 -> ../../vda2` |
| `by-partlabel` | the GPT partition entry's name | |
| `by-id` | the hardware's own identity: model and serial, or WWN | `nvme-QEMU_NVMe_Ctrl_peiosnvme1 -> ../../nvme0n1` |
| `by-path` | the bus position the device sits at | |
| `by-diskseq` | the kernel's monotonic disk sequence number, for this boot only | |

Which one to use depends on what you mean. A *filesystem* is `by-uuid` — it follows the data if the disk is cloned, and it is what `root=UUID=` on the kernel command line names. A *partition* independent of what is on it is `by-partuuid`. A *physical disk* whatever is written to it is `by-id`. `by-label` is the human-friendly choice, but labels need not be unique. A filesystem clone also carries its UUID; verify which device a UUID resolves to when copies may be attached.

Partitions appear under the same keys with the parent's identity plus `-partN`, so `by-id/nvme-…-part2` is the second partition of that NVMe disk.

## Where they are not available

**The initramfs has none of them.** No device manager runs there — only a single pass that loads drivers, described in [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage). The initramfs still honours `root=UUID=`, but it resolves the UUID by probing each block device directly rather than by looking in `/dev/disk/by-uuid`, and `lsblk` does the same. That is why the installer's cmdline works on a machine the initramfs has never seen: it never depended on the links.

**`by-diskseq` does not survive a reboot.** The sequence number is assigned in the order devices appear during *this* boot, which is precisely the property the other directories exist to avoid depending on. It is there for tools that need to tell a re-plugged device from the one it replaced.

## Who creates them

The names are made by the **device manager**, eudev, which peinit starts first in phase 2 of boot. As each block device appears — at boot, when it replays the kernel's enumeration, and afterwards whenever a device is plugged in — the device manager probes it (its partition table, and the filesystem signature on each partition) and creates the matching links. Unplug the device and the links go away.

That is the same daemon that loads a driver for each device the kernel reports, so a disk behind a modular controller gets its driver, its kernel name and its stable names from one pass. See [Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes) for where the service sits in the boot order; a service that opens a device by stable name should `Requires` it, because peinit does not release eudev's dependents until the boot-time replay has finished.

The same idea applies to network interfaces. The kernel names them `eth0`, `eth1` in probe order; the device manager renames each one by where it sits — `enp0s3` for the card in PCI slot 3 on bus 0, `eno1` for an onboard port the firmware numbers — so a configuration written against the name survives a second card or a driver that probes faster next time. `net.ifnames=0` on the kernel command line turns the renaming off.

The device manager does not decide who may open a device. That is the security descriptor on the node, seeded on `/dev` before any of this runs — see [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

## Where to go next

For writing a partition table that gives every partition a `by-partuuid` name, read [Partitioning](~peios/disks-and-filesystems/partitioning).

For how the installer records the root filesystem's UUID into the kernel command line, read [Installing to disk](~peios/disks-and-filesystems/installing-to-disk).

---
title: Identifying Devices
type: how-to
description: Match a saved storage reference to the intended filesystem, partition, or physical disk.
---

Before a mount or destructive operation, compare the selected device's size,
model, partition layout, and live use. Kernel names such as `/dev/sda` and
`/dev/nvme0n1` can change with discovery order.

| Identity | What it follows |
|---|---|
| Filesystem UUID | The filesystem; a clone can duplicate it. |
| Partition UUID | The partition table entry, independently of its filesystem. |
| Hardware ID | The device's advertised serial or worldwide identity. |
| Bus path | The device's position in the hardware topology. |
| Label or partition label | A human-selected name that need not be unique. |
| Disk sequence | An instance in this boot, not a persistent reference. |

The device manager exposes applicable links under `/dev/disk/by-*`. Check the
resolved target, especially when clones are attached. A stable name does not
prove that erasing the target is appropriate.

Do not assume those links exist in an initramfs without the device manager.
A boot hook can resolve `root=UUID=` by probing devices directly. Check the
image's actual discovery path. A real-root service depending on the links
needs the appropriate device-manager dependency, plus handling for removal
or discovery failure.

Device naming does not authorize opening the node. Its security descriptor
and operation-specific checks still apply. Interface renaming similarly
provides a configuration name, not proof of network identity or trust.

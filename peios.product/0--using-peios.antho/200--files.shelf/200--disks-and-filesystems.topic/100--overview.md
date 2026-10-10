---
title: Disks and filesystems
type: how-to
description: Identify storage safely, choose a partitioning or formatting workflow, and inspect filesystem and security-descriptor state.
related:
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/disks-and-filesystems/mke2fs
  - peios/disks-and-filesystems/installing-to-disk
  - peios/mount-policies/overview
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/mount-policies/mount
  - peios/security-descriptors/overview
---

Start with the disk's identity and current use. Partitioning and formatting can
destroy data; a familiar device name is not enough to identify the target.

```sh
part list
lsblk
mount
```

Compare size, model/serial where available, partition layout and mount points.
Use [Disk Manager](~peios/disks-and-filesystems/disk-manager) for a desktop
inspection, and [Stable device names](~peios/disks-and-filesystems/stable-device-names)
for references that must survive a reboot. Unreadable contents are unknown,
not evidence that a disk is blank.

> [!WARNING]
> The device paths in these guides are examples. Before any partition-table
> write or format, verify the whole disk or partition, preserve data you need,
> and release mounts and other users of that device. Never run an example
> against a disk merely because its name matches the page.

## Where to start

| What you need to do | Guide |
|---|---|
| Inspect disks, partitions and mounts on the desktop | [Disk Manager](~peios/disks-and-filesystems/disk-manager), currently inspection-only |
| Diagnose block or inode pressure without changing data | [Find why a filesystem is full](~peios/disks-and-filesystems/diagnose-storage-pressure) |
| Write or inspect a GPT | [Partitioning](~peios/disks-and-filesystems/partitioning) |
| Create an ext filesystem with its root permissions already present | [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors) and [`mke2fs`](~peios/disks-and-filesystems/mke2fs) |
| Copy the live system onto bootable storage | [Installing to disk](~peios/disks-and-filesystems/installing-to-disk) |
| Record a filesystem, partition or hardware identity | [Stable device names](~peios/disks-and-filesystems/stable-device-names) |
| Attach existing storage and choose missing-SD behaviour | [Mount policies](~peios/mount-policies/overview) |
| Explain a file in a merged system directory | [StrataFS](~peios/disks-and-filesystems/stratafs/overview) |

## Where this sits in a running system

`debugfs` is the tool to reach for when you want to inspect an image *offline* — without mounting it, and therefore without KACS being involved at all. It reads and writes extended attributes directly, which makes it the way to confirm that a security descriptor really landed on disk:

```
debugfs -R "ea_list <2>" /dev/vda2
```

Inode 2 is always the root directory of an ext filesystem, so this asks what extended attributes the filesystem's root carries.

`e2fsck` has a specific place in boot. Checking and repairing the root filesystem is the initramfs's job, not peinit's — by the time peinit runs, the root is already mounted, and a filesystem checker cannot repair a filesystem that is in use. See [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage).

## FAT and the EFI system partition

The reason Peios ships FAT tooling at all is the **EFI system partition**. UEFI requires the ESP to be FAT, so a system that cannot format FAT cannot create its own boot partition.

An ESP is also the clearest case of a filesystem that holds no access control of its own. There is no extended-attribute channel, so no security descriptor is ever written to it, and none can be. Its entire access policy comes from the mount — necessarily one of the synthesising classes, since `facs_deny_missing` on a filesystem where every file is permanently missing an SD would make the whole partition unreachable. See [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

The practical consequence: the protection on your boot partition is the mount policy and the physical security of the disk, not a descriptor on the files. Treat the contents accordingly.

## What is not here yet

**Partition tables other than GPT.** `part` writes GPT and only GPT. Peios boots through UEFI with no bootloader, so MBR has nothing to do on a Peios system — but a disk that already carries one is recognised and named rather than silently overwritten. Resizing, moving and MBR↔GPT conversion do not exist either. See [Partitioning](~peios/disks-and-filesystems/partitioning).

**Filesystems other than ext2/3/4 and FAT.** The mount side understands XFS, Btrfs and NTFS as well — see [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem) — but Peios ships creation tools only for the ext and FAT families.

## What ships

| Package | Contents |
|---|---|
| `net.sourceforge.e2fsprogs` | The tools below. |
| `net.sourceforge.e2fsprogs-devel` | Headers, linker symlinks and pkg-config files for building against the libraries. |
| `net.sourceforge.e2fsprogs-static` | Static archives. |
| `net.sourceforge.e2fsprogs-libext2fs`, `net.sourceforge.e2fsprogs-libe2p`, `net.sourceforge.e2fsprogs-libcom-err`, `net.sourceforge.e2fsprogs-libss`, `net.sourceforge.e2fsprogs-libuuid` | The runtime shared libraries, packaged separately so a consumer can depend on one without pulling the tools. |

The tools themselves:

| Tool | Purpose |
|---|---|
| `mke2fs`, `mkfs.ext2`, `mkfs.ext3`, `mkfs.ext4` | Create a filesystem. This is where Peios security descriptors enter. |
| `e2fsck`, `fsck.ext2`, `fsck.ext3`, `fsck.ext4`, `fsck` | Check and repair a filesystem. |
| `tune2fs` | Change parameters on an existing filesystem, including enabling features after the fact. |
| `resize2fs` | Grow or shrink a filesystem. |
| `dumpe2fs` | Print superblock and block-group information. |
| `debugfs` | Interactive low-level access to a filesystem image, including reading and writing extended attributes directly. |
| `blkid`, `findfs` | Identify filesystems by label, UUID or type. |
| `e2label`, `e2image`, `e2undo`, `e2freefrag`, `filefrag`, `badblocks`, `logsave` | Labelling, imaging, undo, fragmentation and block-scanning utilities. |
| `chattr`, `lsattr` | Read and set ext2/3/4 inode attributes. |
| `uuidgen` | Generate a UUID. |

`net.sourceforge.e2fsprogs-libuuid` comes from e2fsprogs;
`org.kernel.libblkid` comes from util-linux. The split is arbitrary but fixed:
each library has exactly one owning package, so the two sources never both ship
the same file.

From `dosfstools`:

| Tool | Purpose |
|---|---|
| `mkfs.fat`, `mkfs.vfat`, `mkfs.msdos` | Create a FAT12/16/32 filesystem. |
| `fsck.fat`, `fsck.vfat`, `fsck.msdos` | Check and repair a FAT filesystem. |
| `fatlabel` | Read or set a FAT volume label. |

The pre-4.0 aliases (`mkdosfs`, `dosfsck`, `dosfslabel`) are deliberately not shipped — they exist for compatibility with a command-line history Peios does not have.

## Where these tools live

The user-facing filesystem tools above are installed in **`/usr/bin`**, reached as `/bin` through the runtime view. See [Install destinations](~peios/advanced-peios/pspu/package-format-and-repository-protocol/install-destinations) for the broader package-layout policy.

The `fsck` dispatcher also uses type-specific checker names in **`/usr/libexec/fsck/`**, exposed through `/libexec/fsck`:

```
/libexec/fsck/fsck.ext2   fsck.ext3   fsck.ext4
                fsck.fat    fsck.vfat   fsck.msdos
```

These backend paths are the dispatch interface: `fsck` picks `fsck.<type>` for the filesystem type it detects or is given. The checker can also have a direct operator interface: `e2fsck` remains in `/usr/bin`, and `fsck.fat` remains there with the `fat`, `vfat` and `msdos` backend names linking to it. This layout is explicit in the pinned [e2fsprogs recipe](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/net.sourceforge.e2fsprogs/pekit.toml#L144-L162) and [dosfstools recipe](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/io.github.dosfstools.dosfstools/pekit.toml#L98-L105). `fsck` searches `/libexec/fsck` first, then the directories on your `PATH`, so a third-party checker installed elsewhere on `PATH` is still found.

The `mkfs.<type>` names stay directly available in `/usr/bin`: Peios ships no `mkfs` front-end.


## Why these tools are packaged, not rewritten

Peios ships upstream **e2fsprogs** for ext2/3/4 and **dosfstools** for FAT.
The on-disk formats remain Linux-compatible. e2fsprogs has Peios additions for
security descriptors; dosfstools has no functional patch because FAT has no
xattr channel in which to store one.

Filesystem creation and offline repair operate below the mounted access-control
layer. `mount` is where a filesystem enters KACS and receives its policy.
Peios-specific tools such as `mount`, `lsblk` and `ls` use that security model;
rewriting the formatters and checkers would instead duplicate upstream format
and repair logic without changing this boundary.

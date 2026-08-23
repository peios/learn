---
title: Disks and filesystems
type: concept
description: The tools Peios ships for creating, checking and inspecting ext2/3/4 and FAT filesystems, and why they are packaged from upstream rather than rewritten.
related:
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/disks-and-filesystems/mke2fs
  - peios/disks-and-filesystems/installing-to-disk
  - peios/mount-policies/overview
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/mount-policies/mount
  - peios/security-descriptors/overview
---

Creating a filesystem is the one operation that happens *before* Peios has any say over it. A block device holds bytes; a filesystem is a structure imposed on those bytes; only when that structure is mounted does the kernel begin making access decisions about what it contains. Everything on this page happens on the early side of that line.

Peios ships two upstream families: **e2fsprogs** for ext2/3/4, and **dosfstools** for FAT. Both are the tools you know from any Linux system. e2fsprogs carries a small Peios patchset, and the one place it diverges is security descriptors, which [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors) covers. dosfstools carries no functional patch at all, for a reason worth stating up front: a FAT filesystem has no extended attributes, so it has nowhere to keep a security descriptor and there is nothing for that work to extend.

## Why these tools are packaged, not rewritten

Most user-facing commands on Peios come from peiosutils, which reworks each tool for the Peios security model — `mount` grew a `policy=` option, `lsblk` reports SD-derived owner and mode, `ls` reads SDs rather than POSIX modes. `mkfs` and `fsck` are deliberately not in that set.

The reason is where the security seam falls. **`mount` is the seam**: it is the operation that takes a filesystem and places it under KACS, choosing the mount policy that governs every access from that point on. `mkfs` and `fsck` sit below the seam. They write and repair a Linux-compatible on-disk format that Peios deliberately mirrors byte for byte — an ext4 filesystem made on Peios is an ext4 filesystem, readable anywhere. Rewriting them would mean reimplementing a format Peios does not want to change, and taking on the correctness burden of a filesystem checker for no security benefit.

So Peios packages e2fsprogs from upstream and carries a patch series for the one thing upstream has no concept of.

## What ships

| Package | Contents |
|---|---|
| `e2fsprogs` | The tools below. |
| `e2fsprogs-devel` | Headers, linker symlinks and pkg-config files for building against the libraries. |
| `e2fsprogs-static` | Static archives. |
| `libext2fs`, `libe2p`, `libcom-err`, `libss`, `libuuid` | The runtime shared libraries, packaged separately so a consumer can depend on one without pulling the tools. |

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

`libuuid` comes from e2fsprogs; `libblkid` comes from the util-linux libraries. The split is arbitrary but fixed — each library has exactly one owning package, so the two sources never both ship the same file.

From `dosfstools`:

| Tool | Purpose |
|---|---|
| `mkfs.fat`, `mkfs.vfat`, `mkfs.msdos` | Create a FAT12/16/32 filesystem. |
| `fsck.fat`, `fsck.vfat`, `fsck.msdos` | Check and repair a FAT filesystem. |
| `fatlabel` | Read or set a FAT volume label. |

The pre-4.0 aliases (`mkdosfs`, `dosfsck`, `dosfslabel`) are deliberately not shipped — they exist for compatibility with a command-line history Peios does not have.

## Where these tools live

Everything above is in **`/usr/bin`**, reached as `/bin` through the runtime view. None of it is in `/sbin`: that is for daemons, which appear in service definitions, and a filesystem tool is a privileged binary a person runs.

The `fsck.<type>` backends are the exception, and they sit in **`/usr/libexec/fsck/`**:

```
/libexec/fsck/fsck.ext2   fsck.ext3   fsck.ext4
                fsck.fat    fsck.vfat   fsck.msdos
```

These are not commands you type. `fsck` picks a checker by exec'ing `fsck.<type>` for the filesystem type it detects or is given, so they are a private interface between the front-end and its backends — which is exactly what `libexec` distinguishes. `fsck` searches `/libexec/fsck` first, then the directories on your `PATH`, so a third-party checker installed elsewhere on `PATH` is still found.

The `mkfs.<type>` names stay in `/usr/bin` for the opposite reason: Peios ships no `mkfs` front-end, so nothing ever dispatches on them and they are only ever typed.

## FAT and the EFI system partition

The reason Peios ships FAT tooling at all is the **EFI system partition**. UEFI requires the ESP to be FAT, so a system that cannot format FAT cannot create its own boot partition.

An ESP is also the clearest case of a filesystem that holds no access control of its own. There is no extended-attribute channel, so no security descriptor is ever written to it, and none can be. Its entire access policy comes from the mount — necessarily one of the synthesising classes, since `facs_deny_missing` on a filesystem where every file is permanently missing an SD would make the whole partition unreachable. See [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

The practical consequence: the protection on your boot partition is the mount policy and the physical security of the disk, not a descriptor on the files. Treat the contents accordingly.

## Where this sits in a running system

`debugfs` is the tool to reach for when you want to inspect an image *offline* — without mounting it, and therefore without KACS being involved at all. It reads and writes extended attributes directly, which makes it the way to confirm that a security descriptor really landed on disk:

```
debugfs -R "ea_list <2>" /dev/vda2
```

Inode 2 is always the root directory of an ext filesystem, so this asks what extended attributes the filesystem's root carries.

`e2fsck` has a specific place in boot. Checking and repairing the root filesystem is the initramfs's job, not peinit's — by the time peinit runs, the root is already mounted, and a filesystem checker cannot repair a filesystem that is in use. See [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage).

## What is not here yet

**Partition tables other than GPT.** `part` writes GPT and only GPT. Peios boots through UEFI with no bootloader, so MBR has nothing to do on a Peios system — but a disk that already carries one is recognised and named rather than silently overwritten. Resizing, moving and MBR↔GPT conversion do not exist either. See [Partitioning](~peios/disks-and-filesystems/partitioning).

**Filesystems other than ext2/3/4 and FAT.** The mount side understands XFS, Btrfs and NTFS as well — see [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem) — but Peios ships creation tools only for the ext and FAT families.

## Where to start

For the security-descriptor model — why a filesystem you intend to keep should carry a real SD from the moment it is created, and how the tree gets one — read [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors).

For the exact command surface, including the extended options and the Peios defaults baked into the binary, read [`mke2fs`](~peios/disks-and-filesystems/mke2fs).

For how these tools are put to work copying a live system onto a disk that then boots itself, read [Installing to disk](~peios/disks-and-filesystems/installing-to-disk).

For what happens to a filesystem once it is attached to the mount tree, read [Mount policies](~peios/mount-policies/overview).

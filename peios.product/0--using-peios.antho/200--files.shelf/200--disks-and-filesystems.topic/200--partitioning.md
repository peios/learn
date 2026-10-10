---
title: Partitioning
type: how-to
description: Inspect disks, write a GPT only after confirming the destructive target, and handle partition reread and safety-check failures.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/disks-and-filesystems/mke2fs
  - peios/mount-policies/sd-storage-by-filesystem
---

Use `part list` to inspect storage before making changes. Use `part` to create,
add or remove **GPT** partitions only after confirming the target whole disk
and the data you intend to discard. Peios boots through UEFI; `part` does not
manage MBR, resize or move partitions, or convert between MBR and GPT.

> [!WARNING]
> A partition-table write has no undo in `part`. Back up needed data and check
> the disk's identity, size, existing contents and mount state. A safety refusal
> is a reason to stop and inspect, not an instruction to add `--force`.

## Listing disks

Run `part list` with no arguments to see every disk on the machine:

```
# part list
DEVICE             SIZE  CONTENTS
/dev/vda           8.0G  gpt, 2 partitions
  vda1             512M  esp    EFI system partition
  vda2             7.5G  linux  Peios root
/dev/vdb           8.0G  no partition table
```

This is the view to start from, because it answers the question that precedes every other one: which disk did you mean? The partition names are the ones the kernel actually created — `vda1` on a virtio or SATA disk, `nvme0n1p1` on an NVMe one — so they are what you can pass straight to `mkfs` or to the installer.

The structure here comes from the kernel, not from reading a partition table, so a disk carrying a format `part` cannot manage still shows its partitions. A disk it cannot read at all is still listed, with `?` for its contents — the disk you cannot read is exactly the one worth knowing about.

Name a disk to see it in full:

```
# part list /dev/vda
/dev/vda: 16777216 sectors of 512 bytes (8.0G)
Label:     gpt
Disk GUID: DE942295-427C-411D-8023-B689D8BEE907
Usable:    34 .. 16777182

  #         START           END        SIZE  TYPE      NAME
  1          2048       1050623        512M  esp       EFI system partition
  2       1050624      16777182        7.5G  linux     Peios root

Free (aligned): 0B  in 0 extent(s), largest 0B
```

`Free (aligned)` counts space a new partition could actually occupy, which is not the same as unallocated sectors — the run below the first alignment boundary can never hold one. Reporting raw free space would promise room that `add` would then refuse to use.

`part verify` checks the same table's structure: both checksums, the two headers agreeing with each other, no overlaps, everything aligned and inside the usable range.

## What it will not do

`part` is the one tool on the system whose mistakes cannot be undone, so it is deliberately hard to point at the wrong thing.

**It requires `--yes`.** There is no interactive "are you sure": the usual caller is a script, and a prompt nobody can answer is worse than no prompt at all.

**It refuses a partition.** Naming `/dev/vda1` where you meant `/dev/vda` would write a GPT *inside* a partition — a table that looks valid to anything reading that partition directly, and is invisible to everything else.

```
# part create /dev/vda1 --yes
part: /dev/vda1 is a partition, not a whole disk; did you mean /dev/vda?
```

**It refuses a disk with anything mounted on it.** Not just the disk itself — any partition of it.

**It refuses a table it did not create.** This is the important one:

```
# part create /dev/vdb --yes
part: this disk carries an MBR (dos) partition table, which part cannot manage;
      pass --force to replace it — every partition on it will be lost
```

`part list` says what it *found*, not merely that it found no GPT — because "no GPT" is ambiguous between a blank disk and a disk holding somebody's data, and those deserve opposite treatment:

| What is there | What `part` says |
|---|---|
| an MBR | "an MBR (dos) partition table, which part cannot manage" |
| an Apple, BSD, Sun or SGI label | names it |
| a GPT whose header is corrupt | "the table may be damaged" |
| a filesystem written straight to the disk | "a `<type>` filesystem … with no partition table" |
| genuinely nothing | "no partition table" |

`--force` is the way through, and it is a *second* confirmation, separate from `--yes`. `--yes` means "I mean this destructive operation"; `--force` means "and I know it destroys a table that was already there". Requiring both is proportionate for an operation with no undo.

## Creating a table

> [!WARNING]
> The following example replaces the target disk's partition layout, then
> creates a 512 MiB ESP and a root partition using the remaining largest run.
> `/dev/vda` is an example whole disk, not a safe default. Confirm its identity,
> preserve any needed data and release all mounted partitions before running
> it. `--yes` is the destructive-operation confirmation; there is no prompt.


```
# part create /dev/vda --yes
/dev/vda: wrote a new GPT (DE942295-427C-411D-8023-B689D8BEE907)

# part add /dev/vda --size 512M --type esp   --name "EFI system partition" --yes
/dev/vda: partition 1 at 2048..1050623 (512M)

# part add /dev/vda --size max  --type linux --name "Peios root" --yes
/dev/vda: partition 2 at 1050624..16777182 (7.5G)
```

`add` puts each partition in the first free run that fits, aligned to 1 MiB. `--size max` takes the largest free run rather than merely the last one, so it still does the obvious thing on a disk with a gap in the middle.

`part del /dev/vda 2 --yes` removes a partition by number. It frees the space and the slot; it does not touch the data that was in it.

### After the table is written

Writing a table changes the disk; it does not by itself change what the kernel believes is on the disk. So `part` asks the kernel to re-read the table, which is what makes `/dev/vda1` appear — without it the partition exists on disk and nowhere else, and the `mkfs` you run next has no path to format.

The kernel refuses to re-read while any partition of the disk is open. Immediately after a write that is usually nothing lasting: publishing the new nodes is what prompts whatever probes new block devices to open one, so the refusal and its cause arrive together. `part` therefore keeps asking for up to three seconds, which outlasts a probe comfortably.

If the disk is still held when that time is up, `part` stops and says what is holding it:

```
# part add /dev/vdb --size max --type linux --name "Peios root" --yes
part: /dev/vdb: the table was written, but the kernel would not re-read it
      within 3000ms: /dev/vdb1 is mounted on /mnt/rootfs. Release it or reboot
      before formatting
```

When nothing of the disk is mounted, it reports that instead. The original
procedure says to run the command again in that case; the table on disk is
already correct and only the kernel's view is behind. Re-inspect the disk before
repeating a mutating command. This guide does not document a separate reread-only
command or establish that repeating `add` is idempotent. Do not format until the
kernel's partition view matches the written table.

### Sizes are sectors unless you say otherwise

`--size` takes `K`, `M`, `G`, `T` — powers of 1024 — or `max`. **A bare number is a sector count, not bytes.** `--size 2048` is 1 MiB on a 512-byte-sector disk, and you can write `2048s` to say so explicitly. Reading it as bytes would silently produce a partition a thousand times smaller than intended.

### Types

`--type` takes a short alias or a raw GUID:

| Alias | Meaning |
|---|---|
| `esp` | EFI system partition |
| `linux` | Linux filesystem data |
| `swap` | Linux swap |
| `msdata` | Microsoft basic data |

The list is short on purpose. Every type GUID in circulation would be a catalogue to keep current, and since a raw GUID is always accepted, nothing is unreachable for want of an alias.

### Names

Up to 36 UTF-16 code units — fewer if you use characters outside the Basic Multilingual Plane, which cost two units each. A longer name is **refused rather than shortened**. A partition name is how you identify the thing you are about to format, and a tool that quietly truncates it makes the label on your screen disagree with the label on the disk.

## Exit status

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | usage error, or the operation failed |
| 2 | could not read or write the device |
| 3 | refused by a safety check |

**3 is separated from 1 on purpose.** A refusal is `part` working correctly, not malfunctioning, and a script should treat "this disk is not what you said it was" differently from "partitioning broke". `peios-install` relies on exactly this distinction.

## Alignment, and why 1 MiB

Every partition starts on a 1 MiB boundary — 2048 sectors on a 512-byte-sector disk, 256 on a 4096-byte one. The number is not arbitrary: 1 MiB divides every erase block and RAID stripe width in practical use, so an aligned partition never straddles one. A misaligned filesystem pays a read-modify-write cycle on every boundary-crossing write, for the life of the filesystem.

`part` reads the logical sector size from the kernel rather than assuming it, so a 4Kn disk gets a correct table rather than one whose every structure is in the wrong place.

## The shape of the tool

If you have used Windows, `part` occupies the slot `diskpart` occupies — but it is not the same shape, and the difference is deliberate.

| | `diskpart` | `part` |
|---|---|---|
| how you use it | an interactive shell: `select disk 0`, then act on it | one command, one device, one job |
| what it covers | partitions, formatting, drive letters, dynamic disks | the partition table |

Everything else `diskpart` bundles already has a home here: [`mke2fs`](~peios/disks-and-filesystems/mke2fs) and `mkfs.vfat` make filesystems, `mount` mounts them, and Peios has no drive letters. And a `select`-then-act model is a hazard in a script, which is what usually calls `part` — a command that acts on "whatever was selected earlier" is one stray line away from acting on the wrong disk.

## Where to go next

To put a filesystem on what you just created, read [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors) and [`mke2fs`](~peios/disks-and-filesystems/mke2fs).

To have the installer do all of this for you, read [Installing to disk](~peios/disks-and-filesystems/installing-to-disk) — `peios-install --whole-disk` runs exactly the three commands above before it formats anything.

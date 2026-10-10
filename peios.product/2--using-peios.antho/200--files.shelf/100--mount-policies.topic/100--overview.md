---
title: Mount policies
type: how-to
description: Choose a mount policy for provisioned storage, removable media or adoption, and check what a policy change affects.
related:
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/mount-policies/managing-mounts
  - peios/mount-policies/mount
  - peios/mount-policies/umount
  - peios/mount-policies/lsblk
  - peios/file-access/overview
  - peios/file-access/the-handle-model
---

Choose a mount policy before attaching a filesystem. It determines what Peios
does when a file has no security descriptor (SD): deny access, derive a temporary
SD, or derive one and save it. A valid stored SD still supplies the file's access
rules, and a corrupt SD is denied under every managed policy.

Start by inspecting the devices and current mounts:

```sh
lsblk
mount
```

Match the intended filesystem to its [stable device
name](~peios/disks-and-filesystems/stable-device-names), then choose a class below.
For a new system filesystem, [format it with an
SD](~peios/disks-and-filesystems/formatting-with-security-descriptors) before
using deny-missing. For an existing volume, check whether its descriptors were
preserved before choosing a strict policy.

## The four classes at a glance

| Your task | Class | Result when an SD is missing |
|---|---|---|
| Use a provisioned system or application filesystem | `facs_deny_missing` | Deny SD-based access. Root, `/home` and `/var` are described as strict system mounts. |
| Read removable media, FAT/exFAT, or a volume whose metadata should remain unchanged | `facs_synthesize_ephemeral` | Derive an SD in memory; do not write it back. A cold inode needs synthesis again. |
| Adopt a filesystem into Peios and store descriptors as files are accessed | `facs_synthesize_persistent` | Derive an SD and schedule write-back. Verify stored SDs before switching to deny-missing. |
| Use kernel pseudo-filesystems such as `/proc` and `/sys` | `unmanaged` | FACS does not apply; the kernel's per-operation checks still do. |

Only the three managed classes are administratively settable. `unmanaged` is
reserved for the kernel, and StrataFS has a fixed deny-missing policy. See
[Policy classes](~peios/mount-policies/policy-classes) for failure and recovery
conditions.

## Why mount policies exist

A managed access check needs an SD, but storage differs: ext4 needs `ea_inode`
for large descriptors, XFS supports large xattrs, tmpfs loses its contents on
unmount, FAT/exFAT cannot store xattrs, and an NFS client may not receive the
server's descriptors. Choose a policy that fits both the filesystem's storage
and whether you intend to change its metadata. Check [SD storage by
filesystem](~peios/mount-policies/sd-storage-by-filesystem) before adopting a
volume.

## Per-superblock, not per-path

The policy belongs to the underlying filesystem instance (the superblock).
All paths and bind mounts sharing that instance share its policy, including a
read-only bind and its read-write source. Binding `/etc/peios` at
`/old/etc/peios` does not create an independent policy boundary.

Separate superblock instances can have different policies. Do not assume that
a second mount of the same device creates one: the
[`mount`](~peios/mount-policies/mount) reference describes superblock reuse and
`--exclusive`, including its restrictions for writable block devices.

## What the policy decides

For managed filesystems, it selects the missing-SD behaviour, the optional
mount-level synthesis template, and whether synthesised SDs are saved.
Synthesis tries parent inheritance, then the mount template, then the fallback.
The class applies to the whole superblock; it is not a per-file permission.

## What the policy does not decide

- File data persistence and available operations still depend on the filesystem.
- Changing policy does not rewrite stored SDs or change already-open handles'
  cached access masks. Future access checks use the new policy.
- A policy change does not propagate into another mounted filesystem below the
  same directory tree.
- Ephemeral SD synthesis does not make the filesystem read-only. Select the
  read-only mount option separately when that is required.

## Where to start

1. Choose the class using [Policy classes](~peios/mount-policies/policy-classes).
2. Check storage and preservation requirements in [SD storage by
   filesystem](~peios/mount-policies/sd-storage-by-filesystem).
3. Use [Managing mounts](~peios/mount-policies/managing-mounts) to apply the
   choice, verify the result and interpret failures.

## The commands

- [`lsblk`](~peios/mount-policies/lsblk): inspect block devices, filesystems and
  SD-derived owner/mode.
- [`mount`](~peios/mount-policies/mount): list mounts, or attach a filesystem
  with `policy=` and an optional synthesis template.
- [`umount`](~peios/mount-policies/umount): detach by mount point or source.
  Read its lazy, forced, recursive and all-targets behaviour before using those
  variants.

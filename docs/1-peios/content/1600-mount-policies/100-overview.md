---
title: Mount policies
type: concept
description: Every mounted filesystem in Peios carries a mount policy — a single setting per superblock that determines whether FACS applies, how missing SDs are handled, and what fallback SD template is used. This page is the map for the four policy classes and where each fits.
related:
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/mount-policies/managing-mounts
  - peios/file-access/overview
  - peios/file-access/the-handle-model
---

A **mount policy** is the per-superblock setting that controls how FACS treats a filesystem. The policy tells the kernel: does FACS apply here at all? When a file has no SD, what should happen? When the kernel synthesises a default SD because the file doesn't have one, where does the template come from? These questions are uniform within a filesystem — every file on a single mount gets the same treatment — and the answer is the mount policy.

There are four policy classes in v0.20. Three are FACS-managed (the kernel applies KACS access control); one is unmanaged (FACS doesn't apply at all). The class is decided when the filesystem is mounted, and changes apply lazily — existing handles are unaffected, but the next access against any file on the mount sees the new policy.

This page introduces the four classes at a glance. [Policy classes](~peios/mount-policies/policy-classes) covers each in detail with the missing-SD and corrupt-SD rules; [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem) covers how each filesystem type physically stores the SD; [Managing mounts](~peios/mount-policies/managing-mounts) covers the syscalls and the generation counter for cache invalidation.

## Why mount policies exist

A FACS-managed file needs a security descriptor. The DACL on it is the access decision input. The kernel needs to be able to look at any FACS-managed file and find an SD.

But not every filesystem can store an SD on every file. ext4 stores SDs in xattrs, but only up to 4 KB without special features; XFS supports xattrs natively up to 64 KB; tmpfs has no persistent storage at all; FAT and exFAT have no xattr support; remote filesystems like NFS may not surface SDs to the client. The kernel needs different behaviours for these cases.

That's what mount policies provide. The policy is the kernel's per-filesystem answer to "what to do when a file does not have an SD I can read":

- For some filesystems, refuse access (the file should have an SD and doesn't, so something is wrong).
- For some, synthesise an SD on the fly in memory (and don't try to write it back).
- For some, synthesise an SD and try to write it back so future accesses don't need to re-synthesise.
- For some (the kernel's own pseudo-filesystems), don't apply FACS at all.

Each of these is one of the four classes. The class is a property of the mount, not the file.

## The four classes at a glance

| Class | What it does | Typical use |
|---|---|---|
| **`facs_deny_missing`** | FACS-managed. A file with no SD is unreachable — every access fails. | System mounts (root, `/home`, `/var`) where every file should have an SD. |
| **`facs_synthesize_ephemeral`** | FACS-managed. A missing SD is synthesised in memory but not written back. The next access re-synthesises. | Removable media, FAT/exFAT, NFS client mounts — filesystems that may not preserve xattrs cleanly or where modifying SDs is not appropriate. |
| **`facs_synthesize_persistent`** | FACS-managed. A missing SD is synthesised and immediately written back. Subsequent accesses use the stored SD. | Filesystems being adopted into Peios — a previously-unmanaged filesystem getting an SD on first access. |
| **`unmanaged`** | FACS does not apply. The kernel uses its own per-operation access rules for files under this mount. | `/proc`, `/sys` — kernel pseudo-filesystems with their own access semantics. |

`unmanaged` is not settable via the public ABI — only the kernel itself sets this class, at boot time, for the pseudo-filesystems it manages. The other three are administratively settable.

A mounted filesystem has exactly one of these classes at any time. Changing the class is a single operation that affects every file on the mount going forward (subject to the lazy-invalidation behaviour).

## Per-superblock, not per-path

A mount policy is per-**superblock**, not per-path or per-bind-mount. All paths visible through the same underlying filesystem instance share the same policy.

The implications:

- A bind mount of `/etc/peios` to `/old/etc/peios` does not let you set different policies for the two paths. They are the same superblock; one policy.
- A read-only bind mount and the underlying read-write mount of the same filesystem share the policy.
- Two separate mounts of the same filesystem (uncommon but possible in some namespacing setups) each have their own superblock instance and can have different policies.

The per-superblock rule keeps mount policy simple. The alternative — per-mount or per-path — would mean a single inode could be subject to different policies depending on how it was reached, which would be operationally confusing.

## What the policy decides

For a FACS-managed mount (any of the three managed classes), the policy decides three things:

1. **What happens when an inode has no SD attached.** Different classes handle this differently — deny, synthesise-in-memory, or synthesise-and-persist.
2. **The mount-level SD template.** Each FACS-managed mount can carry a default SD template, used when synthesising an SD for a file that has no parent-derivable SD (root of the filesystem, typically).
3. **Whether mutations to synthesised SDs are persisted.** Ephemeral synthesises in memory only; persistent writes back to the filesystem.

For the unmanaged class, the policy decides one thing: FACS doesn't apply. Files under this mount are governed by whatever per-operation rules the kernel has for that pseudo-filesystem.

## What the policy does *not* decide

A few clarifications:

- **The policy does not change what filesystem operations are available.** Read, write, mmap, all the usual operations work normally on every class. The policy affects how the *access check* runs, not what operations exist.
- **The policy does not control persistence of file data.** A file's contents are persisted (or not) by the underlying filesystem; the policy is only about SD persistence.
- **The policy does not affect already-open handles.** The handle model caches access masks on fds; changing the policy does not retroactively change cached masks. Future opens see the new policy.
- **The policy does not propagate inheritably.** Changing a parent's mount policy doesn't affect mounted-elsewhere child directories — each mount carries its own policy on its own superblock.

## Where to start

If you want each class in detail — what `facs_deny_missing` actually does at runtime, how `synthesize_ephemeral` works for FAT, what happens when a synthesised SD turns out to be problematic — read [Policy classes](~peios/mount-policies/policy-classes).

If you want to know how each filesystem stores SDs — ext4's `ea_inode`, XFS's native xattr support, NTFS via `system.ntfs_security`, the no-xattr-support filesystems — read [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

If you want the operational story — `kacs_set_mount_policy`, `kacs_get_mount_policy`, the generation counter that makes invalidation lazy, why mount policy changes don't walk the filesystem — read [Managing mounts](~peios/mount-policies/managing-mounts).

---
title: Formatting with security descriptors
type: concept
description: How a filesystem gets real security descriptors at creation time, rather than synthesised ones at mount time, and why that distinction matters.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/mke2fs
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
  - peios/file-access/overview
---

A freshly created filesystem contains one directory — its root — and that directory has no security descriptor. Nothing in the ext4 on-disk format has any concept of one. This is a problem the moment the filesystem is mounted under a FACS-managed policy, because [`facs_deny_missing`](~peios/mount-policies/policy-classes) means exactly what it says: a file with no SD is unreachable, and that includes the root directory you are trying to enter.

There are two ways out. One is to let the kernel invent an SD at mount time. The other is to put a real one on the filesystem when it is created. Peios can do both, and which is appropriate depends on whether the filesystem is something you are passing through or something you intend to keep.

## Synthesised versus stamped

Mount-time synthesis is the right answer for media you do not own. A USB stick formatted on another system, a read-only image, an NTFS volume from Windows — these have no Peios SDs and should not acquire any. `facs_synthesize_ephemeral` gives every inode an SD in memory, derived from the mount's template, and never writes it back.

It is the wrong answer for a filesystem that is going to *be* a Peios system. A synthesised SD is a property of how the filesystem was mounted, not of the filesystem. Mount it with a different template and the whole tree's access policy changes; mount it somewhere that does not set a template and you get whatever the default is. The access policy of a system you own should live on that system, not in the command that attached it.

**Stamping** puts it there. `mke2fs` accepts a security descriptor at format time and writes it to the filesystem's root directory, so the filesystem carries its own policy from the moment it exists and mounts cleanly under `facs_deny_missing` with no template required.

## The root SD, and what it reaches

You give the descriptor as [SDDL](~peios/security-descriptors/overview), and `mke2fs` writes it to the `security.peios.sd` extended attribute on the root directory and on `lost+found`:

```
mke2fs -t ext4 -E root_sddl="O:SYG:SYD:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)" /dev/vda2
```

That descriptor makes SYSTEM the owner and grants both SYSTEM and `BUILTIN\Administrators` full control. The `OICI` flags on each ACE — object-inherit and container-inherit — are what make it reach further than the root directory. Every file and directory subsequently created anywhere on the filesystem derives its own SD from that one through ordinary [inheritance](~peios/security-descriptors/inheritance).

That is worth stating plainly, because it cuts both ways. A single inheritable ACE on the root is, in practice, the access policy of the entire filesystem. It is a complete answer for a system tree where everything should be administrator-owned. It is not a way to express "readable system tree, private home directories" — one inherited ACL cannot say two different things, and the ACEs that would make `/home/alice` private have to come from somewhere else.

When you read an SD, treat the `ID` flag as a diagnostic: `ID` is `INHERITED_ACE`, so that descriptor was derived rather than stored. When you see it, the file's policy is not on the file — go and look at the ancestor it came from.

## Populating a tree with per-node descriptors

Inheritance from the root covers files created *on* the filesystem. It does not cover a tree copied *onto* it, where the nodes already have descriptors of their own that need preserving.

`mke2fs -d` populates a new filesystem from a directory on the build host, and on Peios it is security-descriptor aware. For each node it copies, it computes the SD the node should have in its new home, by combining two inputs:

- The **explicit descriptor** the source node carries — what the creator of that node wanted for it.
- The **parent's descriptor in the new filesystem**, which supplies the inheritable ACEs.

The two are merged by the same rules that govern inheritance on a live system: explicit ACEs first, inherited ACEs appended after them. A node whose source carries no explicit descriptor is left alone, and inherits normally on first access instead. A node whose parent has no descriptor keeps its explicit one verbatim.

The walk is top-down, and directories are stamped before their contents are visited, so every child reinherits against a parent whose descriptor has already been written.

### Why the source uses a different xattr

The explicit descriptor on the source tree is read from **`user.peios.sd`**, not `security.peios.sd`. This looks like an inconsistency and is not.

`security.peios.sd` is the canonical, on-disk home for a descriptor — and precisely because it is canonical, it is protected. On a live Peios filesystem the kernel seals it: direct extended-attribute operations on it are refused unconditionally, and access goes through `kacs_get_sd` and `kacs_set_sd` instead. On a Linux build host, writing anything in the `security.*` namespace needs `CAP_SYS_ADMIN`.

Neither is available to a tool staging a tree. `user.peios.sd` is subject to neither restriction, which makes it the portable carrier: any user can attach it, on any host, and it travels with the tree through ordinary archive and copy operations. `mke2fs -d` reads it, computes the result, and writes the answer to the canonical `security.peios.sd` on the new filesystem. It also skips both names when copying the node's other extended attributes across, so neither the carrier nor a stale canonical value is propagated verbatim.

## This all works offline

None of the above needs a running Peios kernel. The reinheritance computation is pure userspace, and `mke2fs` writes the extended attributes through the ext2 library, addressing the image directly rather than going through the host's filesystem layer. That bypasses the host's own security module and the Peios seal alike, for the simple reason that neither is in the path.

The practical consequence is that a Peios filesystem, with its full security policy in place, can be built on a machine that is not running Peios.

## Where to go next

For the exact syntax of the extended options and the defaults `mke2fs` applies on Peios, read [`mke2fs`](~peios/disks-and-filesystems/mke2fs).

For how a descriptor is physically stored once written, including when an oversized one needs its own inode, read [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

For what the mount policy does with the descriptor you stamped — and what happens on a filesystem that has none — read [Policy classes](~peios/mount-policies/policy-classes).

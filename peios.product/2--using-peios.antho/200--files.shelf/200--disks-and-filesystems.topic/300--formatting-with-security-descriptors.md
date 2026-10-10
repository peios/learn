---
title: Formatting with security descriptors
type: how-to
description: Format a new ext filesystem with a deliberate root ACL, preserve per-node descriptors during population, and verify them before use.
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

For a new Peios system filesystem, give `mke2fs` a root security descriptor at
format time. Without one, the freshly-created root has no SD and normal access
under `facs_deny_missing` fails. A synthesis policy can make missing descriptors
usable, but is a separate choice about how the mount supplies permissions.

Before formatting:

1. Identify the partition using [Partitioning](~peios/disks-and-filesystems/partitioning)
   and [Stable device names](~peios/disks-and-filesystems/stable-device-names).
2. Back up needed data and ensure the target is not in use. Formatting is
   destructive; it is not a repair for one missing descriptor.
3. Choose the root ACL and its inheritance deliberately. A private home tree
   needs per-directory rules; a single root ACL cannot express every policy.
4. If populating from a source tree, check its `user.peios.sd` carriers before
   invoking `mke2fs -d`.

## The root SD, and what it reaches

> [!WARNING]
> `mke2fs` creates a new filesystem and destroys the previous contents of its
> target. Confirm that `/dev/vda2` is the intended unmounted partition before
> using this example. This example grants full control to SYSTEM and
> Administrators; it does not grant ordinary users read access.

You give the descriptor as [SDDL](~peios/security-descriptors/overview), and `mke2fs` writes it to the `security.peios.sd` extended attribute on the root directory and on `lost+found`:

```
mke2fs -t ext4 -E root_sddl="O:SYG:SYD:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)" /dev/vda2
```

That descriptor makes SYSTEM the owner and grants both SYSTEM and `BUILTIN\Administrators` full control. The `OICI` flags on each ACE — object-inherit and container-inherit — are what make it reach further than the root directory. Every file and directory subsequently created anywhere on the filesystem derives its own SD from that one through ordinary [inheritance](~peios/security-descriptors/inheritance).

That is worth stating plainly, because it cuts both ways. A single inheritable ACE on the root is, in practice, the access policy of the entire filesystem. It is a complete answer for a system tree where everything should be administrator-owned. It is not a way to express "readable system tree, private home directories" — one inherited ACL cannot say two different things, and the ACEs that would make `/home/alice` private have to come from somewhere else.

`ID` is `INHERITED_ACE`, so inspect the ancestor when tracing inherited rules.
The original guide also says it means the descriptor is derived rather than
stored. That conflicts with the population path below, which merges inherited
ACEs and writes the result to disk. Do not use `ID` alone as proof that an SD is
absent from storage; validate the stored descriptor separately.


## Verify before mounting

Inspect the unmounted ext filesystem's root xattrs:

```
debugfs -R "ea_list <2>" /dev/vda2
```

The [`mke2fs` example](~peios/disks-and-filesystems/mke2fs#example) shows the
expected `security.peios.sd (96)` entry for the exact descriptor above. Presence
on inode 2 confirms only that root xattr. Inspect child descriptors and intended
access after population as well; do not infer that every source node was stamped.

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


> [!IMPORTANT]
> A node with no source carrier is documented as receiving no stored SD during
> `-d` population. The same guide says it inherits on first access, while
> deny-missing denies missing descriptors. Verify the population and chosen
> mount policy before relying on such a node; this discrepancy is unresolved.

## Synthesised versus stamped

Use ephemeral synthesis for genuinely missing descriptors when the media should
not acquire security metadata, for example files on removable media or a
read-only image. An NTFS volume from Windows may already carry valid stored
SDs; those remain the input to access checks. A corrupt stored descriptor is
denied, not replaced by synthesis.

For a missing SD, synthesis tries parent inheritance, then the mount template,
then the fallback. The result remains in memory under
`facs_synthesize_ephemeral`. Changing a template can change future synthesis
where that template supplies the inputs; it does not replace valid stored SDs
or automatically change the entire tree.

For a filesystem intended to be a Peios system, stamp its policy at creation
rather than relying on missing-descriptor synthesis. `mke2fs` accepts a root SD
and writes it onto the filesystem, so that root has a real descriptor when
mounted under `facs_deny_missing` with no synthesis template required. Verify
populated children separately under the rules above.

## This all works offline

None of the above needs a running Peios kernel. The reinheritance computation is pure userspace, and `mke2fs` writes the extended attributes through the ext2 library, addressing the image directly rather than going through the host's filesystem layer. That bypasses the host's own security module and the Peios seal alike, for the simple reason that neither is in the path.

The practical consequence is that a Peios filesystem, with its full security policy in place, can be built on a machine that is not running Peios.

## Where to go next

For the exact syntax of the extended options and the defaults `mke2fs` applies on Peios, read [`mke2fs`](~peios/disks-and-filesystems/mke2fs).

For how a descriptor is physically stored once written, including when an oversized one needs its own inode, read [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).

For what the mount policy does with the descriptor you stamped — and what happens on a filesystem that has none — read [Policy classes](~peios/mount-policies/policy-classes).

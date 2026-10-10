---
title: SD storage by filesystem
type: how-to
description: Check whether a filesystem can preserve security descriptors, validate copies and restores, and identify policy and storage limitations.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
  - peios/mount-policies/managing-mounts
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/disks-and-filesystems/mke2fs
  - peios/disks-and-filesystems/stratafs/overview
---

Before choosing a mount policy or restoring a backup, check whether the target
can store security descriptors and whether your copy path preserved them.
A successful file-data copy is not enough to make a deny-missing volume usable.

## Validate descriptor preservation

1. Identify the source and destination filesystem types with
   [`lsblk`](~peios/mount-policies/lsblk) and the live mount listing.
2. For mounted files, inspect effective permissions through
   [`sd`](~peios/files-and-directories/sd), which uses the security API.
   This does not establish that an SD is stored: a synthesis mount can return
   a usable in-memory descriptor while the canonical xattr is still absent.
   Direct operations on the canonical SD xattr are sealed.
3. For an offline ext image or unmounted ext filesystem, check the root xattr:

   ```
   debugfs -R "ea_list <2>" /dev/vda2
   ```

   Replace the example device only after identifying the target. This confirms
   presence on inode 2, not validity or coverage of every copied file.
4. Verify stored descriptors on child files and directories as well, using
   filesystem-appropriate offline inspection on an unmounted target; do not
   use mounted `sd` output alone as a persistence test. Include explicit ACLs,
   private data and rarely accessed files. Persistent synthesis schedules
   best-effort write-back, so a successful access is not proof it completed.
   The `mke2fs -d` path uses
   `user.peios.sd` as its source carrier; ordinary canonical-xattr copying is
   not a substitute for that [population
   contract](~peios/disks-and-filesystems/mke2fs#security-descriptor-aware-population).
5. If metadata is missing, choose a deliberate repair/adoption plan before
   enabling deny-missing. If it is corrupt, synthesis will not repair it.

The sections below retain filesystem-specific storage details. Where the
operator guide and kernel reference disagree, the discrepancy is called out;
verify the deployed version before depending on that behaviour.

## The canonical xattr

For filesystems that support extended attributes, Peios stores the SD in the **`security.peios.sd`** xattr. The name is in the `security.*` namespace, which requires privileged access to read or write at the filesystem layer — which doesn't matter for FACS-managed access (FACS denies direct xattr operations on the SD xattr unconditionally; access goes through `kacs_get_sd` / `kacs_set_sd`), but does mean the xattr survives operations that respect security xattrs.

For NTFS, the xattr name is **`system.ntfs_security`** — the native NTFS security attribute, accessed through the same xattr interface. Using the NTFS-native name means SDs round-trip cleanly between Peios and other operating systems that read NTFS.

The choice of xattr name is filesystem-specific:

| Filesystem | xattr name |
|---|---|
| ext4, XFS, Btrfs, tmpfs, others with generic xattr support | `security.peios.sd` |
| NTFS (via the `ntfs3` driver) | `system.ntfs_security` |

For other filesystems (with no xattr support or no convention), the SD is held in memory and re-synthesised on each cold open. See the per-filesystem sections below.

## ext4

ext4 supports xattrs in the inode body and in a separate xattr block. The
inode's available inline space is not 4 KB: it depends on inode size and other
metadata. The separate block is commonly 4 KiB and also has overhead and may
hold other attributes. See the [upstream ext4 storage
layout](https://kernel.org/doc/html/latest/filesystems/ext4/attributes.html).

The **`ea_inode`** feature stores a large xattr value in a separate inode when
it does not fit in the inode body or external block; see [large extended
attribute values](https://kernel.org/doc/html/next/filesystems/ext4/eainode.html).
The Peios guide documents support up to the 65,535-byte SD limit with this
feature, enabled at creation or later through `tune2fs`.

`mke2fs` on Peios enables `ea_inode` by default for ext4, and raises the inode size to 512 bytes so that a typical SD fits inline in the first place — see [`mke2fs`](~peios/disks-and-filesystems/mke2fs). Complex or deeply inherited ACLs can outgrow the available xattr space;
`ea_inode` accommodates large values without assuming a universal inline limit.

If an ext4 filesystem without `ea_inode` cannot fit an SD in its available
inode-body or external-block xattr space, the filesystem's xattr write fails. The kernel handles this by either:

- Refusing the `kacs_set_sd` call with an error indicating the filesystem cannot hold the SD.
- Or, in the `facs_synthesize_persistent` case, refusing the write-back and treating the file as if it has no SD (re-synthesising next time).

Check whether `ea_inode` is enabled when large descriptors cannot be stored.
Do not assume that a typical descriptor fitting inline proves every descriptor
on the volume will fit.

## XFS

XFS supports xattrs natively, up to 64 KB per attribute by default. This is comfortably more than the SD size limit (65,535 bytes), so SDs fit without any special configuration.

XFS is a fine choice for FACS-managed filesystems. No `ea_inode`-style consideration is needed; SDs just work.

## Btrfs

Btrfs supports xattrs, but do not assume any practical SD size will fit.
[Upstream Btrfs documents xattr items in tree leaves](https://btrfs.readthedocs.io/en/stable/dev/On-disk-format.html#xattr-item-18),
with attributes sharing a name hash required to fit in one leaf. This does not
support the original guide's claim that large xattrs receive their own extents.
Peios-specific support for larger descriptors has not been verified. Validate
the actual descriptor sizes on the target before depending on a restore or
persistent-synthesis workflow.

Btrfs's snapshot and clone behaviour is interesting for SDs: a Btrfs snapshot of a directory includes the SDs of every file within. A snapshot is a point-in-time view; the SDs in the snapshot reflect what they were when the snapshot was taken. If the original files' SDs are subsequently modified, the snapshot still has the old SDs. This is the expected behaviour but worth noting for backup/snapshot workflows.

## tmpfs and devtmpfs

> [!WARNING]
> The original guidance below describes ephemeral synthesis and udev-provided
> descriptors. The [kernel reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#kernel-internal-mounts)
> instead documents deny-missing defaults for `TMPFS_MAGIC`, including
> devtmpfs, with kernel-seeded roots. Confirm the mounted instance's actual
> policy and descriptors; do not assume udev or synthesis supplied them.


tmpfs is an in-memory filesystem. It supports xattrs, but everything it stores lives in RAM and is lost on unmount or reboot. SDs on tmpfs are present while the filesystem is mounted; they vanish when it is unmounted.

tmpfs is typically mounted with `facs_synthesize_ephemeral`. The synthesis happens in memory anyway (the tmpfs storage *is* memory), so there's no operational difference between "store an SD in the tmpfs xattr" and "synthesise an SD into the kernel's per-inode cache".

`devtmpfs` is the kernel-managed filesystem for device nodes. SDs on devtmpfs are applied by **udev rules**, not by FACS-driven synthesis. The udev daemon (or its Peios equivalent) sets the SD on each device node as the node is created. This is a different model from the synthesis-based pattern other filesystems use; it works because the device-node population is controlled centrally and the SDs can be set deterministically.

devtmpfs uses the `facs_synthesize_ephemeral` class, but in practice the synthesis path is rarely hit because udev provides the SDs.

## NTFS — round-trip via ntfs3

> [!NOTE]
> An unknown principal and a missing descriptor are not interchangeable. The
> guide's rationale below mentions unrecognised Windows principals; the
> [kernel reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#xattr-protection)
> identifies a specific missing-`$Secure` case. A valid stored SD is evaluated;
> a corrupt one is denied even under ephemeral synthesis.


NTFS is the Windows-native filesystem. Peios mounts it through the **`ntfs3`** kernel driver, which exposes the NTFS security attribute via the standard xattr interface under the name `system.ntfs_security`.

The implications:

- SDs written by Peios to an NTFS volume use the same on-disk format as Windows. A Windows system reading the same volume sees the SD natively.
- SDs written by Windows to an NTFS volume are readable by Peios. Round-tripping a volume between the two operating systems preserves SDs.

This is the "binary-compatible" property the SD format gives. The wire format is the same; the filesystem driver translates between the xattr interface and the on-disk security attribute.

NTFS volumes are typically mounted `facs_synthesize_ephemeral` rather than `facs_deny_missing`. The reasoning: an NTFS volume from Windows may have files without Peios-recognised SDs (the SDs are Windows-native and may use principals that don't exist on the Peios system). Ephemeral synthesis lets such files be accessible without modifying the volume's stored SDs.

## FAT and exFAT

FAT and exFAT have **no xattr support at all**. There is no place to store an SD; the on-disk format simply doesn't have the metadata channel.

FACS handles this by using `facs_synthesize_ephemeral` for FAT/exFAT mounts. Every file gets a synthesised SD in memory; no SD is ever written back. The synthesised SD applies for the file's time in the inode cache; when the file is evicted, the SD is gone and will be re-synthesised on next access.

This means FAT/exFAT files cannot be given persistent KACS-style permissions. The synthesised SD is the same every time (assuming the same inputs — parent SD, mount template), so the access decision is deterministic, but there is no way to customise per-file.

For most FAT use cases this is fine — FAT is typically used for removable media or boot partitions where uniform-permissions semantics is acceptable. The mount-level SD template can be configured to grant whatever access pattern is appropriate for the mount as a whole.

## NFS — synthesise locally, enforce remotely

NFS client mounts are a unique case. The actual files live on a remote server; the local filesystem driver is a network protocol implementation, not a real filesystem.

The mount class is `facs_synthesize_ephemeral`. FACS synthesises a local SD per the synthesis chain (typically yielding a sensible default from the mount template) and uses it for local access control. The local FACS check decides whether to forward the operation to the server.

If the local check passes, the operation goes to the server. The server has its own access control (potentially also Peios with FACS, potentially another OS with different rules); the server's access control decides whether the operation actually proceeds. If the server denies, the operation fails with whatever error the protocol returns (typically `-EACCES` or `-EIO`).

This is "dual authority" — both client and server have a say. The client's denial is local-final; the server's denial is remote-final. There is no single source of truth for the access decision.

The implications were covered in [Special cases](~peios/file-access/special-cases) under "NFS — dual authority": don't trust local FACS results for security, expect I/O errors from server-side denial, the local synthesised SD is not the server's actual SD.

## /proc and /sys

`/proc` and `/sys` are kernel pseudo-filesystems. Their mount-policy class is `unmanaged` — set by the kernel at boot, not changeable via the public ABI.

`/proc` doesn't have an SD per-file in the FACS sense. Access to `/proc/<pid>/*` is gated by the per-process rules (process SD + PIP, from the two-check rule). The kernel implements these checks directly when serving `/proc` file operations.

`/sys` similarly has its own per-file rules. The `/sys/kernel/security/kacs/*` entries have explicit SDs the kernel maintains; other `/sys` files have hardcoded rules ("writes restricted to `BUILTIN\Administrators` and `SYSTEM`").

The `unmanaged` class is what tells FACS to not interfere with these. The kernel knows what it is doing with its own pseudo-filesystems; FACS stays out of the way.

## Stacked filesystems — overlayfs and StrataFS

> [!WARNING]
> The forwarding description below includes StrataFS, but the [StrataFS kernel
> contract](~peios/advanced-peios/peios-kernel/stratafs/security/mount-policy#missing-descriptors)
> says it does not ask a provider's policy to synthesise a missing descriptor:
> access through StrataFS is denied. Do not rely on a readable direct stratum
> path proving the merged path is readable. The live-boot example also assumes
> an explicitly synthesising squashfs; the [kernel default](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#boot-artifacts)
> is deny-missing and requires descriptors in the image.


A stacking filesystem presents files that physically live somewhere else. overlayfs merges a read-only lower layer with a writable upper one; [StrataFS](~peios/disks-and-filesystems/stratafs/overview) composes several directories into one view. Neither stores a security descriptor of its own, and neither needs to: the descriptor belongs to the file, and the file is on the layer underneath.

So a stack forwards. When the kernel needs the SD of a file in the merged view, it asks the layer that actually holds it, and what comes back is that layer's **effective** descriptor — which is to say, whatever an access check on the underlying file would have used. If the layer underneath *stores* an SD, the stack sees the stored one. If the layer underneath *synthesises*, the stack sees the synthesised one. Synthesis composes upward through the stack; it is not a private arrangement between the kernel and the bottom layer.

That is what makes the common live-boot arrangement work:

```
overlay          <- the merged root, facs_deny_missing
  upper: tmpfs   <- writable scratch, stores real SDs
  lower: squashfs <- read-only image with no SDs, facs_synthesize_ephemeral
```

The overlay stores nothing and can still be `facs_deny_missing`, because neither layer beneath it ever answers "missing": the tmpfs has stored descriptors, and the squashfs synthesises one for every inode.

Two consequences worth holding onto:

**The stack's own policy class governs only what happens when every layer beneath it has nothing to offer.** Pick it for that case. Over a synthesising lower, `facs_deny_missing` is the strict-and-correct choice; over an `unmanaged` lower it would lock the whole view.

**A copy-up does not carry the lower's descriptor up with it.** When overlayfs copies a file from the lower layer to the upper to make it writable, it creates a genuinely new inode in the upper, and that inode gets its descriptor by ordinary [inheritance](~peios/security-descriptors/inheritance) from its parent in the upper — not by duplicating the lower's. This is deliberate: `security.peios.sd` is not userspace-writable (SD mutation is `kacs_set_sd`'s job), so a verbatim copy could not be performed even in principle, and the inherited answer is the right one anyway. Every other extended attribute *is* copied up normally.

## Summary

| Filesystem | SD storage | Typical mount class |
|---|---|---|
| ext4 | `security.peios.sd` xattr; `ea_inode` for large values | `facs_deny_missing` (for system mounts) |
| XFS | `security.peios.sd` xattr, native large support | `facs_deny_missing` |
| Btrfs | `security.peios.sd` xattr; verify size limits | `facs_deny_missing` |
| tmpfs | `security.peios.sd` xattr in memory | `facs_synthesize_ephemeral` |
| devtmpfs | xattr in memory, populated by udev | `facs_synthesize_ephemeral` |
| NTFS (ntfs3) | `system.ntfs_security` xattr, NTFS-native | `facs_synthesize_ephemeral` (typical) |
| FAT / exFAT | No SD storage; in-memory only | `facs_synthesize_ephemeral` |
| NFS client | No client-side storage; synthesise locally | `facs_synthesize_ephemeral` |
| squashfs | No SD storage unless the image was built with one | `facs_synthesize_ephemeral` |
| overlayfs | None of its own — reads the real layer | `facs_deny_missing` |
| StrataFS | None of its own — reads the provider | `facs_deny_missing`, not settable |
| /proc | n/a — no FACS | `unmanaged` |
| /sys | n/a — kernel-managed SDs | `unmanaged` |

Treat the table as the original guide's typical-policy summary, not proof of the policy on a running mount. tmpfs/devtmpfs, squashfs and StrataFS have important source discrepancies noted above. Read back the actual policy before relying on it.

## Where to go next

For what each policy class does with a missing SD, read [Policy classes](~peios/mount-policies/policy-classes).

For setting and reading a mount's policy at runtime, read [Managing mounts](~peios/mount-policies/managing-mounts).

For the structure of the SD being stored, read [Security descriptors](~peios/security-descriptors/overview).

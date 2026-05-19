---
title: SD storage by filesystem
type: concept
description: Different filesystems store SDs differently. ext4 uses xattrs, sometimes needing the ea_inode feature for larger SDs. XFS supports xattrs natively. NTFS rounds-trip through system.ntfs_security. FAT and exFAT have no xattr support at all. This page catalogues the storage by filesystem type and the implications for mount-policy choice.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
  - peios/mount-policies/managing-mounts
  - peios/security-descriptors/overview
---

A security descriptor is structurally a single piece of metadata that has to live somewhere. Different filesystems have different ways to hold metadata; some have built-in security-attribute support (NTFS), some have generic extended attribute support that fits (ext4, XFS, Btrfs), some have neither (FAT, exFAT). The mount-policy class you choose for a filesystem depends partly on what the filesystem can store and partly on what behaviour you want.

This page covers the storage mechanism each filesystem type uses and the implications.

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

ext4 supports xattrs natively. SDs up to about 4 KB fit in the inline xattr space; larger SDs require the **`ea_inode`** feature.

`ea_inode` is an ext4 feature that lets a single xattr value spill into a dedicated inode rather than being limited to the size of the inode's inline xattr area. With `ea_inode` enabled at filesystem creation time (or enabled later via `tune2fs`), an SD can be up to the standard 65,535-byte SD limit.

Peios images are formatted with `ea_inode` enabled by default. Real-world SDs rarely exceed the inline xattr space, but pathological cases (deeply-nested ACEs, lots of inherited ACEs from a complex parent) can push past 4 KB; `ea_inode` accommodates them.

If an ext4 filesystem without `ea_inode` is mounted on Peios and a file has an SD larger than its inline xattr space could hold, the filesystem's xattr write would fail. The kernel handles this by either:

- Refusing the `kacs_set_sd` call with an error indicating the filesystem cannot hold the SD.
- Or, in the `facs_synthesize_persistent` case, refusing the write-back and treating the file as if it has no SD (re-synthesising next time).

The cleanest fix is to enable `ea_inode`. For everyday use, the inline xattr space is sufficient.

## XFS

XFS supports xattrs natively, up to 64 KB per attribute by default. This is comfortably more than the SD size limit (65,535 bytes), so SDs fit without any special configuration.

XFS is a fine choice for FACS-managed filesystems. No `ea_inode`-style consideration is needed; SDs just work.

## Btrfs

Btrfs supports xattrs natively. Small xattrs are stored inline; larger ones get their own extent. SDs of any practical size fit without special handling.

Btrfs's snapshot and clone behaviour is interesting for SDs: a Btrfs snapshot of a directory includes the SDs of every file within. A snapshot is a point-in-time view; the SDs in the snapshot reflect what they were when the snapshot was taken. If the original files' SDs are subsequently modified, the snapshot still has the old SDs. This is the expected behaviour but worth noting for backup/snapshot workflows.

## tmpfs and devtmpfs

tmpfs is an in-memory filesystem. It supports xattrs, but everything it stores lives in RAM and is lost on unmount or reboot. SDs on tmpfs are present while the filesystem is mounted; they vanish when it is unmounted.

tmpfs is typically mounted with `facs_synthesize_ephemeral`. The synthesis happens in memory anyway (the tmpfs storage *is* memory), so there's no operational difference between "store an SD in the tmpfs xattr" and "synthesise an SD into the kernel's per-inode cache".

`devtmpfs` is the kernel-managed filesystem for device nodes. SDs on devtmpfs are applied by **udev rules**, not by FACS-driven synthesis. The udev daemon (or its Peios equivalent) sets the SD on each device node as the node is created. This is a different model from the synthesis-based pattern other filesystems use; it works because the device-node population is controlled centrally and the SDs can be set deterministically.

devtmpfs uses the `facs_synthesize_ephemeral` class, but in practice the synthesis path is rarely hit because udev provides the SDs.

## NTFS — round-trip via ntfs3

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

## Summary

| Filesystem | SD storage | Typical mount class |
|---|---|---|
| ext4 | `security.peios.sd` xattr; `ea_inode` for SDs > 4 KB | `facs_deny_missing` (for system mounts) |
| XFS | `security.peios.sd` xattr, native large support | `facs_deny_missing` |
| Btrfs | `security.peios.sd` xattr, native | `facs_deny_missing` |
| tmpfs | `security.peios.sd` xattr in memory | `facs_synthesize_ephemeral` |
| devtmpfs | xattr in memory, populated by udev | `facs_synthesize_ephemeral` |
| NTFS (ntfs3) | `system.ntfs_security` xattr, NTFS-native | `facs_synthesize_ephemeral` (typical) |
| FAT / exFAT | No SD storage; in-memory only | `facs_synthesize_ephemeral` |
| NFS client | No client-side storage; synthesise locally | `facs_synthesize_ephemeral` |
| /proc | n/a — no FACS | `unmanaged` |
| /sys | n/a — kernel-managed SDs | `unmanaged` |

The pattern: real on-disk filesystems with xattr support get one of the `facs_*` classes depending on policy needs. Pseudo-filesystems and the kernel's own filesystems are `unmanaged`. Filesystems without xattr support default to ephemeral synthesis as the only viable mode.

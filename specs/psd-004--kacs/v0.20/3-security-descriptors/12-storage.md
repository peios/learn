---
title: SD Storage
---

Security Descriptors MUST be stored alongside the objects they protect. The storage mechanism depends on the object type.

## Files and directories

SDs are stored as filesystem extended attributes (xattrs) in the self-relative binary format. The canonical xattr name is `security.peios.sd`. On NTFS volumes, KACS uses `system.ntfs_security` (the ntfs3 driver's native SD xattr) so that SDs round-trip between Peios and other operating systems.

The underlying filesystem MUST support extended attributes of at least 65,535 bytes per value. The architectural maximum SD size is 65,535 bytes.

| Filesystem | Large xattr mechanism | Notes |
|---|---|---|
| ext4 | ea_inode feature | Required for SDs > 4 KB. Peios images are formatted with ea_inode enabled. |
| XFS | Native | Up to 64 KB natively. |
| Btrfs | Native | Inline or extent-backed. |
| tmpfs | In-memory | Size limited by available memory. |
| devtmpfs | In-memory | Device SDs applied by udev rules. |
| NTFS (ntfs3) | `$SECURE` / `system.ntfs_security` | SDs round-trip with other operating systems. |
| FAT/exFAT | No xattr support | Synthesize mode only. |

## Registry keys

SDs are stored by loregd alongside the key data. The format is the same self-relative binary blob. Access control is enforced by loregd impersonating the client and calling AccessCheck via the KACS syscall.

## Kernel objects

Tokens, processes, and logon sessions store SDs inline on the kernel object. These SDs are typically small (a few ACEs) and are set at object creation time.

Logon sessions receive a default kernel-object SD at creation time:

```
Owner: <session user SID>
Group: <creator's effective token primary group SID>
DACL:
  ALLOW  <session user SID>       GENERIC_ALL
  ALLOW  BUILTIN\Administrators   GENERIC_ALL
  ALLOW  SYSTEM                   GENERIC_ALL
```

For kernel-created logon sessions that have no creator token, the group is the
session user SID. The logon-session SD is stored for object-shape parity and
future management APIs only. In `v0.20`, no access-control decision depends on
`auth_id`, AccessCheck MUST NOT consult logon-session SDs, and no separate
mutation or query path exists for logon-session SDs.

## IPC endpoints

SDs are stored by the service that owns the endpoint. Pathname sockets use the socket file's inode SD. Abstract sockets store the SD on the socket's LSM security blob, set at `bind()` time from the binding thread's effective token.

For abstract sockets, the stamped SD is a volatile default kernel-object SD:

```
Owner: <creator's effective token user SID>
Group: <creator's effective token primary group SID>
DACL:
  ALLOW  <creator's user SID>      GENERIC_ALL
  ALLOW  BUILTIN\Administrators     GENERIC_ALL
  ALLOW  SYSTEM                      GENERIC_ALL
```

No separate mutation path exists in `v0.20` for abstract-socket blob SDs. The
bind-time default SD is the only SD the abstract socket receives.

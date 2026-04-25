---
title: File SD Storage
---

## Xattr protection

FACS intercepts all raw xattr operations on the canonical SD xattr (`security.peios.sd`, or `system.ntfs_security` on NTFS):

- **Writes denied.** Any attempt to write the SD xattr via `setxattr()` MUST be denied. All SD modification MUST go through the set-security interface.
- **Removal denied.** Any attempt to remove the SD xattr MUST be denied. SDs MUST NOT be detached from files.
- **Reads denied.** Any attempt to read the SD xattr via `getxattr()` MUST be denied. The raw xattr contains the entire SD including the SACL — allowing reads with only READ_CONTROL would leak SACL content that SHOULD require ACCESS_SYSTEM_SECURITY. All SD reads MUST go through `kacs_get_sd`.

## SD caching

FACS caches the parsed SD in the inode's LSM security blob.

**Readers** (the AccessCheck path) use RCU read-side locks. No locks, no atomics, no contention.

**Writers** (the set-security syscall) allocate a new parsed SD, swap the pointer atomically via RCU, and free the old SD after a grace period. No partial reads are possible.

**Population** is lazy — on first access. The xattr is read via an internal kernel path that bypasses the read-denial hook. After parsing, the result is installed via compare-and-swap. If another thread races, the loser frees its copy.

**Invalidation** happens atomically with writes. The set-security syscall is the sole writer — after writing the xattr, it installs the new parsed SD. There is no window where xattr and cache disagree.

**Eviction** frees the cached SD when the kernel evicts the inode, using an RCU-safe callback to ensure in-flight permission checks complete before the SD is freed.

## Missing SDs

FACS handles files without a `security.peios.sd` xattr with a per-mount policy:

### Deny mode

No SD means deny all FACS-managed access. This is the default for Peios system mounts (root, `/home`, `/var`). A missing SD on a system mount is a corruption indicator.

**Directory traversal exception:** SeChangeNotifyPrivilege (granted to all by default) bypasses traverse checks, including on directories with missing SDs. This ensures path resolution works for the repair path.

**O_PATH exception:** O_PATH opens bypass `security_file_open` entirely. A file with a missing SD can still be acquired as an O_PATH reference, enabling the repair path: `open(path, O_PATH)` → `kacs_set_sd(fd, ..., AT_EMPTY_PATH)` with SeRestorePrivilege.

### Synthesize mode

No SD means generate a default SD on the fly. For foreign mounts — USB drives, external volumes, NFS client mounts. Synthesis sources, evaluated in order:

1. **Inherit from parent directory.** If the parent has an SD, FACS runs the inheritance algorithm as if a new file were being created.
2. **Mount-level template.** A default SD configured in the mount options. Applied when there is no parent SD — typically only the mount root. If no mount-level template is configured, the fallback SD grants GENERIC_ALL to SYSTEM (`S-1-5-18`) and BUILTIN\Administrators (`S-1-5-32-544`), with GENERIC_READ | GENERIC_EXECUTE to Everyone (`S-1-1-0`). Owner is SYSTEM, group is SYSTEM.

**Persistence flag:** each mount carries a `persist_synthesized` setting:

- `true` (adopting foreign media) — the synthesized SD is written to xattr immediately. Synthesis happens once.
- `false` (removable media) — cached in the inode blob only, never written to disk. The original filesystem remains unmodified.

## Corrupt SDs

A `security.peios.sd` xattr that exists but fails structural validation is a corrupt SD.

**Policy: fail-closed.** A corrupt SD MUST deny all access. AccessCheck MUST NOT be called. A truncated DACL MUST NOT be treated as empty.

**Audit:** every corrupt SD encounter SHOULD emit an audit event. The event fires once per inode per cache population to avoid spam.

**Recovery:** a process with SeRestorePrivilege calls the set-security syscall to overwrite the corrupt SD. Offline repair tools MAY also rewrite xattrs directly on unmounted filesystems.

## NFS client mounts

NFS client mounts are a distinct mount class where FACS's sole-authority guarantee does not hold:

- The NFS server enforces its own access control independently. FACS evaluates locally against the synthesized SD, but the server MAY deny I/O that FACS allowed.
- A locally authorized `open()` MAY produce an fd whose `read()` calls fail because the server denies the I/O.

This is inherent to network filesystems with server-side enforcement.

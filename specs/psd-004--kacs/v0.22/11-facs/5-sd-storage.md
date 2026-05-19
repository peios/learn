---
title: File SD Storage
---

## Xattr protection

FACS intercepts all raw xattr operations on the canonical SD xattr (`security.peios.sd`, or `system.ntfs_security` on NTFS):

- **Writes denied.** Any attempt to write the SD xattr via `setxattr()` MUST be denied. All SD modification MUST go through the set-security interface.
- **Removal denied.** Any attempt to remove the SD xattr MUST be denied. SDs MUST NOT be detached from files.
- **Reads denied.** Any attempt to read the SD xattr via `getxattr()` MUST be denied. The raw xattr contains the entire SD including the SACL — allowing reads with only READ_CONTROL would leak SACL content that SHOULD require ACCESS_SYSTEM_SECURITY. All SD reads MUST go through `kacs_get_sd`.

## SD caching

FACS caches a validated parsed-SD object in the inode's LSM security blob. The
cached object MUST include immutable self-relative SD bytes and prevalidated
component layout sufficient for AccessCheck readers to avoid reparsing
untrusted storage bytes.

**Readers** (the AccessCheck path) use the RCU-published cache pointer. Once a
current cache entry exists, readers MUST NOT take the inode mutex merely to run
AccessCheck. A reader MAY either complete the evaluation under an RCU read-side
critical section or pin the cache object with a refcount while still under RCU
and then drop the RCU read lock before running code that can allocate, sleep,
emit audit events, or otherwise perform side effects. Refcount-pinned readers
MUST acquire the pin with a non-zero refcount check and MUST drop the pin after
the operation.

**Writers** (the set-security syscall) allocate a new parsed-SD cache object,
swap the pointer atomically via RCU, and free the old object after an RCU grace
period and after any reader pins have drained. No partial reads are possible.

**Population** is lazy — on first access. The xattr is read via an internal kernel path that bypasses the read-denial hook. After parsing, the result is installed via compare-and-swap. If another thread races, the loser frees its copy.

**Invalidation** happens atomically with writes. The set-security syscall is the sole writer — after writing the xattr, it installs the new parsed SD. There is no window where xattr and cache disagree.

**Eviction** frees the cached SD when the kernel evicts the inode, using an
RCU-safe callback and reader-pin draining to ensure in-flight permission checks
complete before the SD is freed.

## Mount policy classes

Every mounted filesystem visible to FACS exposes exactly one mount-policy class:

- `unmanaged` — the mount is outside the ordinary FACS handle model. FACS does not synthesize missing SDs and does not stamp granted masks on ordinary file handles from this mount. `/proc` and `/sys` use this class in `v0.22`.
- `facs_deny_missing` — the mount is FACS-managed and missing SDs deny access.
- `facs_synthesize_ephemeral` — the mount is FACS-managed and missing SDs are synthesized but not written back automatically.
- `facs_synthesize_persistent` — the mount is FACS-managed and missing SDs are synthesized and written back immediately.

For kernel purposes, the superblock policy object carries the mount-policy
class and an optional mount-level default SD template for synthesize-class
mounts.

## Mount policy administration

Trusted userspace components such as `peinit`, a udev-equivalent policy agent,
or a future LCS-backed mount-policy daemon MAY adopt a mounted filesystem by
calling `kacs_set_mount_policy` on an fd that names any object on the target
superblock. `O_PATH` fds are valid targets. The operation changes the policy for
the superblock, not for the particular pathname used to reach it.

`kacs_set_mount_policy` requires enabled SeTcbPrivilege and MUST mark
SeTcbPrivilege used on success. The public ABI accepts only managed policy
classes: `facs_deny_missing`, `facs_synthesize_ephemeral`, and
`facs_synthesize_persistent`. Attempts to set `unmanaged`, unknown policy
values, non-zero reserved flags, or malformed arguments MUST fail closed.

The optional mount-level template is accepted only with synthesize-class
policies. It is a complete self-relative file SD, not a subset SD. If supplied,
it MUST pass structural SD validation and MUST be no larger than 64 KiB.
Supplying a null template pointer with length 0 clears the template. Setting
`facs_deny_missing` clears the template and rejects non-empty template input.
Pointer/length mismatches and invalid SD bytes fail before policy state is
changed.

Policy changes are lazy. They do not recursively walk the filesystem and do not
stamp every file. The superblock policy object carries a monotonic generation
counter. Each successful policy or template replacement increments the
generation. Missing-SD and ephemeral-synthetic inode cache entries record the
generation they were derived from; when the generation changes, those entries
MUST be discarded and repopulated on next use. Xattr-backed valid SD caches and
corrupt-SD caches are not made valid by policy changes. Existing open file
descriptions retain their immutable granted masks.

## Missing SDs

FACS handles files without a `security.peios.sd` xattr according to the mount-policy class:

### `facs_deny_missing`

No SD means deny all FACS-managed access. This is the default for Peios system mounts (root, `/home`, `/var`). A missing SD on a system mount is a corruption indicator.

**Directory traversal exception:** SeChangeNotifyPrivilege (granted to all by default) bypasses intermediate path-resolution traverse checks, including on directories with missing SDs. This ensures path resolution works for the repair path. It does not bypass explicit `chdir()` / `chroot()` or `fchdir()` use-time checks.

**O_PATH exception:** O_PATH opens bypass `security_file_open` entirely. A file with a missing SD can still be acquired as an O_PATH reference, enabling the repair path: `open(path, O_PATH)` → `kacs_set_sd(fd, ..., AT_EMPTY_PATH)` with SeRestorePrivilege.

### `facs_synthesize_ephemeral` and `facs_synthesize_persistent`

No SD means generate a default SD on the fly. For foreign mounts — USB drives, external volumes, NFS client mounts. Synthesis sources, evaluated in order:

1. **Inherit from parent directory.** If the parent has an SD, FACS runs the inheritance algorithm as if a new file were being created.
2. **Mount-level template.** A default SD configured in the mount options. Applied when there is no parent SD — typically only the mount root. If no mount-level template is configured, the fallback SD grants GENERIC_ALL to SYSTEM (`S-1-5-18`) and BUILTIN\Administrators (`S-1-5-32-544`), with GENERIC_READ | GENERIC_EXECUTE to Everyone (`S-1-1-0`). Owner is SYSTEM, group is SYSTEM.

Because these files already exist, the current accessor's token is not the
creator for synthesis purposes. When the inheritance algorithm needs creator
inputs (owner SID, primary group SID, default DACL), FACS uses a synthetic
system-policy creator:

- if a mount-level template exists, its owner, group, and DACL provide the
  creator inputs
- otherwise, the fallback SD above provides the creator inputs

The current accessor's token MUST NOT affect the synthesized file SD.

Class-specific persistence behavior:

- `facs_synthesize_persistent` (adopted foreign media) — the synthesized SD is written to xattr immediately. Synthesis happens once.
- `facs_synthesize_ephemeral` (removable media, FAT/exFAT, NFS client mounts) — the synthesized SD is cached in the inode blob only and MUST NOT be written back automatically. The original filesystem remains unmodified.

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

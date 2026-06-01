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

### Default policy by filesystem type

In the absence of an explicit `kacs_set_mount_policy` call, FACS MUST select a
default mount-policy class from the superblock's filesystem magic. The
following defaults apply in `v0.22`:

- `PROC_SUPER_MAGIC`, `SYSFS_MAGIC` — `unmanaged`. These pseudo-filesystems
  expose kernel state through inode-shaped handles that have no meaningful
  on-disk identity and no SD to consult; ordinary FACS access checks do not
  apply.
- `NULL_FS_MAGIC` (nullfs) — `unmanaged`. nullfs is the immutable,
  permanently-empty filesystem the kernel mounts as the mount-namespace root,
  with the mutable rootfs mounted on top of it (see `Initial SDs on
  kernel-internal mounts` below). It declares no xattr support
  (`s_xattr == NULL`), so it can never carry a `security.peios.sd` SD, and its
  single root inode is immutable and childless — there is nothing to stamp and
  nothing to protect. As with `/proc` and `/sys`, ordinary FACS access checks
  do not apply.
- `RAMFS_MAGIC`, `NFS_SUPER_MAGIC`, `MSDOS_SUPER_MAGIC`, `EXFAT_SUPER_MAGIC` —
  `facs_synthesize_ephemeral`. These either have no persistent backing at all
  (ramfs) or live on storage that has no native SD slot (FAT family, NFS
  client mounts).
- Any other magic, including `TMPFS_MAGIC`, `SQUASHFS_MAGIC`, and native disk
  filesystems such as `EXT4_SUPER_MAGIC` and `BTRFS_SUPER_MAGIC` —
  `facs_deny_missing`. These can all carry the `security.peios.sd` xattr
  natively and are expected to do so on every inode that participates in
  access checks.

This mapping is a default. Trusted userspace MAY override the class for any
superblock via `kacs_set_mount_policy` (see below).

Note that `TMPFS_MAGIC` covers both userspace tmpfs mounts and the
kernel-mounted tmpfs instances established before any userspace runs
(initial rootfs and devtmpfs). The latter are handled by the seeding
requirement in `Initial SDs on kernel-internal mounts` below; they are not
exempted from the default.

## Initial SDs on kernel-internal mounts

Two filesystems are mounted by the kernel itself before any userspace process
exists and before any trusted component has had the opportunity to call
`kacs_set_mount_policy` or `kacs_set_sd`:

- the mutable root filesystem mounted by `init_mount_tree`, which is a tmpfs
  in the `v0.22` kernel configuration (`CONFIG_TMPFS=y` and no `root=` /
  `rootfstype=` override). Under the Linux 7.0 mount model `init_mount_tree`
  mounts this tmpfs (mount id 2) on top of an immutable `nullfs` namespace
  root (mount id 1); the tmpfs is what `set_fs_root` makes `/` and what the
  initramfs is unpacked into, and it is the inode seeded below. The nullfs
  root is not seeded — it is `unmanaged` by the magic mapping above, being
  permanently empty and incapable of xattr storage;
- the devtmpfs instance mounted by `devtmpfs_init` and populated by the
  `kdevtmpfs` kernel thread.

Both use `TMPFS_MAGIC` and therefore default to `facs_deny_missing`. Their
root inodes are created by the kernel and never traverse a userspace-supplied
artifact, so they contain no `security.peios.sd` xattr at the moment they
become reachable.

To make `facs_deny_missing` viable for these mounts, the kernel MUST write an
initial self-relative file SD to the `security.peios.sd` xattr of each root
inode at the moment the mount is established and before any task — kernel or
userspace — can act on it:

- the rootfs root inode is seeded inside `init_mount_tree` immediately after
  `vfs_kern_mount` returns successfully and before the new mount is published
  into `init_mnt_ns`, with the inode's `i_rwsem` held;
- the devtmpfs root inode is seeded inside `devtmpfs_init` immediately after
  `vfs_kern_mount` returns successfully and before `kdevtmpfs` is started,
  with the inode's `i_rwsem` held.

The seeded SD MUST be identical in both cases and MUST be:

- owner = group = `SYSTEM` (`S-1-5-18`);
- a DACL containing a single `ACCESS_ALLOWED` ACE granting `GENERIC_ALL` to
  `SYSTEM`, flagged `OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE` so the
  inheritance algorithm derives a child SD for every inode subsequently
  created on that mount;
- no SACL.

Writes MUST happen through the kernel-internal xattr path that bypasses both
the FACS read/write denial hooks and the LSM permission hook for setxattr.
They MUST NOT consult the current task's token, because at the point either
seed runs there may not be a meaningful subject token; the seeded SD is the
sole authority for the mount until trusted userspace replaces it. They MUST
NOT depend on FACS being fully initialised beyond the LSM scaffold that
allocates inode and superblock security blobs.

These SDs are not exempt from subsequent management. Trusted userspace MAY
overwrite the per-inode SD via `kacs_set_sd` or change the per-superblock
policy class via `kacs_set_mount_policy` once it has the privileges to do so.

## Boot artifacts and offline-built filesystems

Filesystems shipped as boot artifacts — a squashfs payload concatenated into
the initrd, a vendor squashfs delivered as a peipkg, a partition image
flashed onto a disk — default to `facs_deny_missing` under the magic mapping
above and the kernel does not seed their inodes. They are already-populated
trees that the kernel cannot extend with SDs at mount time, and in the
read-only case (squashfs) cannot extend at all.

The build pipeline that produces such an artifact MUST emit
`security.peios.sd` xattrs on every regular file, directory, and other inode
that ordinary access checks will reach. `mksquashfs`, ext utilities, and the
standard userland xattr surfaces preserve `security.*` xattrs natively; the
obligation is on the artifact builder, not the kernel and not the consuming
mount.

A boot artifact that fails to carry SDs on its files is a packaging defect.
FACS treats every missing SD on a `facs_deny_missing` mount as a corruption
indicator and denies access. The operator path is to either rebuild the
artifact with SDs or to call `kacs_set_mount_policy` on the affected
superblock to adopt it under a synthesize-class policy.

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

No SD means deny all FACS-managed access. This is the default class for any
superblock not mapped elsewhere by `Default policy by filesystem type` above
— in practice tmpfs, squashfs, and native disk filesystems. A missing SD on
a `facs_deny_missing` mount is a corruption or packaging indicator; the only
expected source of newly-mounted `facs_deny_missing` filesystems without SDs
is the kernel-internal mounts covered by `Initial SDs on kernel-internal
mounts`, and those are seeded before any task can observe them missing.

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

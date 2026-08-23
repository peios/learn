---
title: File Descriptor Storage
description: Where a file's descriptor lives and why raw xattr access is denied in all three directions — plus caching, mount policy classes and boot artifacts.
---

## Xattr protection

FACS intercepts every raw xattr operation on the canonical descriptor
xattr — `security.peios.sd`, or `system.ntfs_security` on NTFS — and
denies all three directions.

**Writes** are denied: all modification goes through the set-security
interface. **Removal** is denied: a descriptor is never detached from
a file. And **reads** are denied, which is the least obvious of the
three and the most important. The raw xattr holds the entire
descriptor including the SACL, so allowing a read under
`READ_CONTROL` alone would leak SACL content that properly requires
`ACCESS_SYSTEM_SECURITY`. All reads go through `kacs_get_sd`, which
distinguishes the two.

## Caching

A validated, parsed descriptor object is cached in the inode's LSM
blob, holding immutable self-relative bytes together with a
prevalidated component layout — enough for AccessCheck readers never
to reparse untrusted storage bytes.

**Readers** on the AccessCheck path use the RCU-published pointer.
Once a current entry exists, a reader does not take the inode mutex
merely to run AccessCheck. It either completes the evaluation inside
an RCU read-side critical section, or pins the object with a refcount
while still under RCU and drops the RCU lock before doing anything
that can allocate, sleep or emit an audit event. A pin is acquired
with a non-zero refcount check and dropped afterwards.

**Writers** allocate a new object, swap the pointer atomically, and
free the old one after a grace period and after reader pins have
drained. No partial read is possible.

**Population** is lazy, on first access. The xattr is read through an
internal kernel path that bypasses the read-denial hook, and the
parsed result is installed by compare-and-swap; a thread that loses
the race frees its own copy.

**Eviction** frees the cached descriptor when the inode is evicted,
through an RCU-safe callback with the same pin draining, so in-flight
permission checks complete before the object goes away.

**Invalidation** happens on write, but not atomically with it. The
set-security path deliberately releases the inode security lock across
the xattr write and re-acquires it afterwards to publish the new
parsed object, because holding it across the write would invert the
`i_rwsem` ordering the access path requires. Two concurrent
set-security calls on one inode are therefore last-writer-wins rather
than serialised end to end, and there is a window in which the xattr
and the cache disagree. Readers are never blocked, and no reader sees
a partially written object — the exposure is which of two racing
writes lands, not a torn state.

## Mount policy classes

The superblock policy object carries the class (§3.9.1) and, for
synthesise-class mounts, an optional mount-level default template.

The default classifier maps from the superblock's filesystem magic.
`PROC_SUPER_MAGIC` and `SYSFS_MAGIC` are **unmanaged**: these expose
kernel state through inode-shaped handles with no on-disk identity and
no descriptor to consult. `NULL_FS_MAGIC` is unmanaged too — nullfs is
the immutable, permanently empty filesystem the kernel mounts as the
mount-namespace root, with the mutable rootfs mounted on top of it. It
declares no xattr support at all, so it can never carry a descriptor,
and its single root inode is immutable and childless: nothing to stamp
and nothing to protect.

`STRATAFS_SUPER_MAGIC` is fixed at **`facs_deny_missing`** for the
superblock's lifetime, because StrataFS delegates every check to
current provider objects and must never synthesise a descriptor for
its merged namespace. An attempt to change it fails with
`EOPNOTSUPP`.

`RAMFS_MAGIC`, `NFS_SUPER_MAGIC`, `MSDOS_SUPER_MAGIC`,
`EXFAT_SUPER_MAGIC`, `ISOFS_SUPER_MAGIC` and `CGROUP2_SUPER_MAGIC` are
**`facs_synthesize_ephemeral`** — either no persistent backing at all,
or storage with no native descriptor slot.

Everything else, including `TMPFS_MAGIC`, `SQUASHFS_MAGIC`,
`EXT4_SUPER_MAGIC` and `BTRFS_SUPER_MAGIC`, defaults to
**`facs_deny_missing`**. These can all carry the descriptor xattr
natively and are expected to on every inode that participates in
access checks.

`TMPFS_MAGIC` covers both userspace tmpfs mounts and the kernel-mounted
instances established before any userspace runs. The latter are not
exempt from the default; they are handled by seeding.

## Kernel-internal mounts

Two filesystems are mounted by the kernel before any userspace process
exists and before anything can call `kacs_set_mount_policy` or
`kacs_set_sd`: the mutable root filesystem mounted by
`init_mount_tree`, a tmpfs mounted on top of the immutable nullfs
namespace root and made `/` by `set_fs_root`; and the devtmpfs
instance mounted by `devtmpfs_init` and populated by the `kdevtmpfs`
thread.

Both are `TMPFS_MAGIC` and therefore `facs_deny_missing`, and their
root inodes are kernel-created, never passing through a
userspace-supplied artifact, so they carry no descriptor at the moment
they become reachable. To make the class viable the kernel seeds one.

The rootfs root is seeded inside `init_mount_tree`, immediately after
`vfs_kern_mount` returns and before the mount is published into
`init_mnt_ns`, with the inode's `i_rwsem` held. The devtmpfs root is
seeded inside `devtmpfs_init`, after `vfs_kern_mount` and before
`kdevtmpfs` starts, likewise under `i_rwsem`. The nullfs root is not
seeded — it is unmanaged, empty, and incapable of xattr storage.

The seeded descriptor is byte-for-byte identical in both places: owner
and group SYSTEM (`S-1-5-18`), a DACL of one `ACCESS_ALLOWED` ACE
granting `GENERIC_ALL` to SYSTEM flagged
`OBJECT_INHERIT_ACE | CONTAINER_INHERIT_ACE` so that inheritance
derives a child descriptor for every inode created on the mount
afterwards, and no SACL.

The writes go through the kernel-internal xattr path, bypassing both
the FACS denial hooks and the LSM setxattr permission hook. They
consult no token — at the point either runs there may be no meaningful
subject — and the seeded descriptor is the sole authority for the
mount until trusted userspace replaces it. They depend on nothing
beyond the LSM scaffold that allocates inode and superblock blobs.

These are not exempt from later management: trusted userspace can
overwrite the per-inode descriptor or change the superblock's class
once it holds the privileges.

## Boot artifacts

A filesystem shipped as a boot artifact — a squashfs concatenated into
the initrd, a vendor squashfs delivered as a package, a flashed
partition image — defaults to `facs_deny_missing` and the kernel does
**not** seed it. These are already-populated trees the kernel cannot
extend at mount time, and in the read-only case cannot extend at all.

The obligation falls on the build pipeline, which emits
`security.peios.sd` on every inode ordinary access checks will reach.
`mksquashfs`, the ext utilities and the standard userland xattr
surfaces all preserve `security.*` natively.

An artifact without descriptors is a packaging defect. FACS treats
every missing descriptor on a `facs_deny_missing` mount as a
corruption indicator and denies. The operator path is to rebuild the
artifact, or to adopt the superblock under a synthesise class.

## Administration

Trusted userspace adopts a mounted filesystem by calling
`kacs_set_mount_policy` on a descriptor naming any object on the
target superblock; `O_PATH` descriptors are valid targets. The change
applies to the superblock, not the pathname used to reach it.

The call requires enabled `SeTcbPrivilege` and marks it used. The
public ABI accepts only the three managed classes; `unmanaged`,
unknown values, nonzero reserved flags and malformed arguments all
fail closed.

The optional template is accepted only with a synthesise class. It is
a complete self-relative descriptor rather than a subset, passes
structural validation, and is at most 65535 bytes. A null pointer with
zero length clears it. Setting `facs_deny_missing` clears it and
rejects non-empty template input. Pointer and length mismatches and
invalid bytes fail before any state changes.

Policy changes are **lazy**. They do not walk the filesystem and do
not stamp anything. The superblock carries a monotonic generation
counter, incremented on every successful policy or template
replacement. Missing-descriptor, ephemeral-synthetic and
not-yet-written-back persistent-synthetic cache entries record the
generation they came from and are discarded and repopulated when it
changes. Xattr-backed and corrupt-descriptor caches are not made valid
by a policy change, and open file descriptions keep their immutable
masks.

## Missing descriptors

Under **`facs_deny_missing`**, no descriptor means deny. Two
exceptions keep the repair path open. `SeChangeNotifyPrivilege`
bypasses intermediate traverse checks including on directories with no
descriptor, though not explicit `chdir()`, `chroot()` or `fchdir()`
use-time checks. And `O_PATH` opens bypass the open hook entirely, so
a file with a missing descriptor can still be acquired as an `O_PATH`
reference — which is exactly the repair route: `open(path, O_PATH)`
then `kacs_set_sd` with `AT_EMPTY_PATH` under `SeRestorePrivilege`.

Under the **synthesise classes**, a missing descriptor is generated
from two sources in order. First, **inheritance from the parent**: if
the parent has one, the inheritance algorithm runs as though a new
file were being created. Otherwise the **mount-level template**,
applied where there is no parent descriptor — typically only at the
mount root. With no template configured, the fallback grants
`GENERIC_ALL` to SYSTEM and `BUILTIN\Administrators` and
`GENERIC_READ | GENERIC_EXECUTE` to Everyone, owned by SYSTEM with
SYSTEM as group.

Because these files already exist, the accessor is not their creator.
Where inheritance needs creator inputs — owner, primary group, default
DACL — a synthetic system-policy creator supplies them: the template's
owner, group and DACL if one exists, the fallback's otherwise. **The
accessor's token never affects the synthesised descriptor**, and the
synthesis path takes no subject token at all.

Inheritance is recursive — a parent whose own descriptor is missing is
synthesised first, walking toward the mount root where the template
terminates it. The walk is bounded at 32 ancestor levels; a target
nested deeper than that below the nearest resolvable ancestor fails
closed with `EACCES` rather than synthesising.

An **ephemeral** synthesis is cached in the inode blob only and never
written back, leaving the original filesystem unmodified. A
**persistent** one is additionally written to the xattr so the medium
acquires durable descriptors — but never inline.

## Deferred write-back

Synthesis runs holding the FACS inode lock, and writing the xattr
takes the inode's `i_rwsem`. Doing that inline would acquire `i_rwsem`
under the FACS lock, inverting the order the access path requires, and
would self-deadlock when synthesis is reached from a metadata
operation whose VFS caller already holds `i_rwsem`. Write-back
therefore runs with no FACS or VFS lock held.

Synthesis caches the descriptor immediately and marks the entry
pending. The access decision is correct from that cached value the
instant synthesis completes — correctness never depends on the xattr
reaching disk. The write-back runs later from a task-work callback
firing as the triggering syscall returns to userspace, so a persistent
descriptor is normally on disk by the time the operation that first
observed it missing returns.

A pending entry is generation-tagged exactly like an ephemeral one, so
a policy or template change before the write-back discards it and
re-synthesises; a stale pre-change descriptor is never pinned to disk.

Write-back is best-effort, and can be because the synthesised
descriptor is a deterministic function of the parent or the template —
the on-disk xattr is a cache of a recomputable value, not unique
state. If it does not happen, because the entry was evicted or the
task exited first, the identical descriptor is re-synthesised on next
access and retried. A failed or skipped write-back never fails the
operation that triggered synthesis. Kernel threads, and a failure to
queue the callback, fall back to re-synthesis the same way.

Once written, the next cache miss reads it back as an ordinary
xattr-backed descriptor: durable, no longer generation-tagged, and
never synthesised again.

An ancestor synthesised only to supply inheritance inputs for a
descendant is itself pending, and persists under the same rules when
it is next accessed in its own right.

## Corrupt descriptors

A descriptor xattr that exists but fails structural validation is
corrupt, and the policy is fail-closed: deny all access, do not call
AccessCheck, and never treat a truncated DACL as an empty one.

Every encounter emits an audit event, fired exactly once per inode per
cache population rather than per access, so a hot corrupt inode does
not flood the log.

Recovery is a process holding `SeRestorePrivilege` calling
set-security to overwrite it. Offline repair tools can also rewrite
xattrs directly on an unmounted filesystem.

## NFS client mounts

NFS is the one managed class where the sole-authority guarantee does
not hold. The server enforces its own access control independently:
FACS evaluates locally against a synthesised descriptor, and the
server may deny I/O that FACS allowed. A locally authorized `open()`
can therefore produce a descriptor whose `read()` calls fail. This is
inherent to network filesystems with server-side enforcement, and
nothing suppresses the server's denial.

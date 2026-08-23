---
title: The Handle Model
description: FACS is the file-specific enforcement surface of KACS — mount policy, scope, how a handle is acquired, and stacked backing files.
---

FACS, the File Access Control Shim, is the file-specific enforcement
surface of KACS. It replaces Linux DAC — UID, GID and mode-bit checks
— with security-descriptor evaluation on files.

Enforcement follows the handle pattern. AccessCheck runs once at open
time, the granted mask is cached on the file description, and later
operations test the cached mask:

```
(fd.granted & required) == required ? allow : deny
```

The mask is set once and never modified, and it is immutable for the
descriptor's whole lifetime regardless of any later descriptor change.
A file's DACL can be rewritten while a process holds it open, and that
process keeps the rights it was granted. A few operations use a live
AccessCheck instead; §3.9.4 lists them.

A second immutable mask is stamped alongside it: the **continuous
audit mask** (§3.8.9), which every use-time operation consults to
decide whether to emit a per-operation audit event. It travels with
the granted mask through every path described below.

## Mount policy

Every mounted filesystem exposes exactly one FACS mount-policy class,
scoped to the kernel superblock object rather than to a pathname or a
bind mount — several paths or bind mounts over one superblock all
observe the same class.

**`unmanaged`** puts the mount outside the handle model entirely: no
granted mask is stamped on its file descriptions. **`facs_deny_missing`**
is FACS-managed and denies access where a descriptor is missing.
**`facs_synthesize_ephemeral`** synthesises missing descriptors and
caches them in memory only. **`facs_synthesize_persistent`**
synthesises them and writes them back immediately. The three `facs_*`
classes are the only managed ones.

The default classifier is conservative. Hardcoded pseudo-filesystems —
`/proc`, `/sys`, nullfs — are `unmanaged`. Filesystems that cannot
reliably store the canonical descriptor xattr are
`facs_synthesize_ephemeral`: FAT, exFAT, NFS client mounts, ISO9660,
and cgroup2. StrataFS is fixed at `facs_deny_missing`. Everything else
— tmpfs, squashfs, ext4, btrfs — defaults to `facs_deny_missing`
unless a trusted policy agent adopts it.

Userspace cannot set a superblock to `unmanaged` through the public
ABI; the class is reserved for the kernel classifier and the hardcoded
rules. Attempting to set a policy on a magic-derived `unmanaged`
superblock fails with `EOPNOTSUPP`, and so does attempting to change
StrataFS's.

## Scope

The sole-authority claim covers local FACS-managed filesystems. It
does not cover `O_PATH` descriptors, which are not managed; NFS client
mounts, which are ephemeral-synthesising and retain dual authority
with the server; `/proc`, which is unmanaged and PIP-protected; or
`/sys`, which is unmanaged and carries a hardcoded rule instead —
writes there require Administrators or SYSTEM, enforced against a
built-in descriptor. Descriptors for processes obtained through
`pidfd` bypass FACS at open as well.

## Handle acquisition

A descriptor carries its granted mask through every acquisition path,
and transfer is an intentional capability-delegation mechanism.
`dup`/`dup3` and `fork` produce the same open file description and
therefore the same rights; descriptors without `FD_CLOEXEC` survive
exec unchanged; `SCM_RIGHTS` transfers the descriptor as a capability
token, with possession as authorization and no re-check of the
receiver's identity; and `pidfd_getfd()` is gated by an AccessCheck
for `PROCESS_DUP_HANDLE` against the target process, after which the
caller receives the descriptor with its full mask.

The security boundary is at open time. Every subsequent transfer
carries the mask unchanged.

This means mandatory subject policy — MIC and PIP — is evaluated once,
at open, against the opener. A high-integrity process that opens a
file and passes the descriptor to a low-integrity one has effectively
delegated its access. That is the handle model: authority is on the
handle, not on the holder.

## Stacked backing files

When a stacking filesystem creates a kernel-private backing file for a
managed user-visible file, the outer file's granted and continuous
audit masks are captured into the backing-file blob, and the backing
file's ordinary blob receives that exact snapshot when the provider is
opened. No new AccessCheck runs against the task executing the
stacking filesystem.

The inheritance is deliberately narrow. It is admitted only through
the kernel's typed backing-file allocation path, only from a managed
non-`O_PATH` outer file, and it retains no reference to that outer
file — only the values. It is not a general snapshot-cloning
mechanism.

An active StrataFS copy-up context takes precedence: a backing open
that does not match its exact object and phase does not fall back to
inherited authority. When an exactly-bound copy-up backing file is
adopted by the outer descriptor, the outer snapshot is installed into
both blobs as a single transition, after which the backing file
behaves like any other stacked open.

The user-visible operation is checked and continuously audited once,
against the outer handle. Immediate provider re-entry through
`security_file_permission` or `security_mmap_file` neither repeats the
caller authorization nor emits a second caller audit event. The
backing file keeps the snapshot for later descriptor-local
enforcement, including `mprotect()` after a stacked mmap, and the
`mmap_backing_file` handoff verifies that the outer, backing and
captured snapshots still agree before the provider mapping is
installed.

This suppresses duplicate *KACS* authorization only. It bypasses
nothing else — not another LSM, not filesystem errors, not read-only
mounts, immutable state, quota, space, I/O, or format validation.

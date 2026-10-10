---
title: Policy classes
type: how-to
description: Choose a missing-descriptor policy, plan an adoption or recovery, and distinguish missing SDs from corrupt ones.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/mount-policies/managing-mounts
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
---

Choose the class for the files you expect to find, then verify that expectation:
use deny-missing for provisioned storage, ephemeral synthesis when SDs must not
be written to the volume, and persistent synthesis to adopt existing files.
Changing class is not a bulk conversion and does not repair corrupt descriptors.

The command-line spellings are `policy=deny-missing`,
`policy=synth-ephemeral` and `policy=synth-persist`; see
[Managing mounts](~peios/mount-policies/managing-mounts) for application and
privilege requirements.

## facs_deny_missing

Use this for a filesystem whose files are expected to carry valid SDs, including
provisioned system mounts such as root, `/home` and `/var`. The base-image build
is expected to supply descriptors, and subsequent creation inherits from the
parent. A restore that skips security metadata breaks that expectation.

A missing SD produces `-EACCES` for operations requiring an SD-based access
check. Ordinary reads, writes, deletion and permission changes can therefore
fail before you can repair the file through the usual path.

> [!IMPORTANT]
> The original operator description says to use `kacs_set_sd` with `WRITE_DAC`,
> while warning that the caller may be unable to acquire the required access.
> The kernel reference separately documents an `O_PATH`/`AT_EMPTY_PATH` repair
> route under `SeRestorePrivilege`, and intermediate-traverse exceptions.
> Follow the [documented repair contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#missing-descriptors)
> for the deployed version; do not assume an inaccessible file can be repaired
> merely by changing its mount policy.

Before switching an adopted volume to this class, verify stored SDs on the files
you need, including files that ordinary usage may never have touched.

## facs_synthesize_ephemeral

Use this when the filesystem cannot store SDs or when reading it must not add
security metadata. Typical uses include removable media, FAT/exFAT and NFS
client mounts. The kernel reads a stored SD if one exists; otherwise it derives
one through the synthesis chain below and uses it for the access check.

The result is cached only while the inode is in memory. It is never written
back. After eviction, a later open synthesises again; unchanged inputs produce
the same SD. This costs work on a cold inode, but leaves on-disk metadata alone.
It does not prohibit writes to file contents: read-only mounting is separate.

Earlier guidance also lists tmpfs/devtmpfs here. The kernel TRM documents
stricter defaults for those filesystems; check the [filesystem-specific
notes](~peios/mount-policies/sd-storage-by-filesystem#tmpfs-and-devtmpfs) rather
than assuming their class.

## facs_synthesize_persistent

Use this to adopt a volume whose missing descriptors should become persistent.
The first access derives an SD, uses the cached value immediately, and schedules
write-back. A later access reads the stored SD after write-back succeeds.

Write-back is deferred until the triggering operation finishes, normally before
its syscall returns to userspace. It is best-effort, not evidence that every
file now has a stored descriptor. If the entry is evicted or the task exits
first, the next access derives the same value and retries. A policy/template
change before write-back discards the pending value and derives against the
new inputs, rather than saving a superseded SD.

This is incremental adoption: regularly used files acquire SDs first;
rarely-used files wait until accessed. Once all required files have stored SDs,
you can switch to deny-missing. Any stragglers become inaccessible to normal
SD-based operations. Existing stored descriptors are unaffected.

For the locking and task-work mechanism, use the [kernel write-back
reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#deferred-write-back).

## unmanaged

This class is reserved for kernel-managed pseudo-filesystems. It skips FACS,
not all security checks:

- `/proc/<pid>/*` uses process-SD and PIP checks under the two-check rule.
- `/sys` uses the kernel's per-operation rules, including writes restricted to
  `BUILTIN\Administrators` and SYSTEM.
- `/sys/kernel/security/kacs/*` has explicit descriptors maintained and read by
  the kernel's own logic.

`kacs_set_mount_policy` rejects `unmanaged` with `-EINVAL`; operators cannot
use it to disable FACS on a regular filesystem. An ephemeral policy with a
permissive template can grant broad access to files missing SDs, but still runs
FACS and must be reviewed as a security change. It is not a substitute for
repairing a broken descriptor.

## The synthesis chain

When a managed synthesis policy finds no SD, it tries these sources in order:

1. Parent-directory inheritance, using inheritable ACEs as for a newly-created
   child. See [Inheritance](~peios/security-descriptors/inheritance).
2. The mount-level template, commonly needed at the filesystem root where no
   parent on that filesystem supplies a usable descriptor.
3. The fallback: owner and group SYSTEM; `GENERIC_ALL` for SYSTEM and
   `BUILTIN\Administrators`; `GENERIC_READ | GENERIC_EXECUTE` for Everyone.

A missing template does not imply private access: the fallback grants other
users read-and-execute. Review the template before exposing a volume. Earlier
notes call the template limit 64 KB; the [kernel
contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#administration)
specifies at most 65,535 bytes.

The [kernel synthesis
reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#missing-descriptors)
also specifies recursive parent synthesis, a 32-ancestor limit that fails
closed with `EACCES`, and creator inputs independent of the accessor's token.
Use that reference for implementation details.

## Corrupt SD handling

A stored SD that fails structural validation produces `-EACCES` under all three
managed classes. Bad headers, malformed ACLs, invalid SIDs and oversized
values do not trigger synthesis. Missing and corrupt are different conditions.

The kernel emits a corruption audit event once per inode per cache population,
not on every repeated access. A restore producing many corrupt SDs may therefore
produce a burst of events as files are first accessed.

Changing to a synthesising policy does not make a corrupt SD valid. Recovery
requires fixing the descriptor or accepting denial. The [kernel repair
reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#corrupt-descriptors)
documents set-security under `SeRestorePrivilege` and offline xattr repair on
an unmounted filesystem.

## Class transitions

| Transition | Check before changing |
|---|---|
| Persistent synthesis to deny-missing | Confirm the required files have stored SDs; files still missing one will be denied. |
| Ephemeral to persistent synthesis | Confirm that saving metadata is intended and supported. Each later missing-SD access saves its newly derived result. |
| Deny-missing to a synthesis class | Treat this as a deliberate relaxation for recovery/adoption. Review the template; corrupt SDs remain denied. |

A transition changes policy only; no files are touched at that moment. Future
accesses re-evaluate stale synthesis state. Existing handles keep their masks,
and stored SDs remain unchanged. See [Managing
mounts](~peios/mount-policies/managing-mounts) before applying the change.

## Where to go next

- [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem):
  verify where descriptors can persist.
- [Managing mounts](~peios/mount-policies/managing-mounts): apply and read back
  the class and template.
- [`mount`](~peios/mount-policies/mount): exact attach-time options.

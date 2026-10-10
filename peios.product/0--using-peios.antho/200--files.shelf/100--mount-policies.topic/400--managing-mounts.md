---
title: Managing mounts
type: how-to
description: Inspect mounts, choose a policy at attach time, verify class and template changes, and troubleshoot policy failures.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/privileges/overview
---

Inspect the current mount and choose its missing-descriptor policy before
changing anything. A policy change affects every path sharing the superblock,
but it does not update stored descriptors or revoke already-open handles.

## Inspect and attach a filesystem

Use these read-only listings first:

```sh
lsblk
mount
```

`mount` lists live state from the kernel; Peios has no `/etc/fstab` or
`/etc/mtab`. The listing is limited to mounts your token may observe. An empty
or partial listing does not prove that a device is unused.

For a new mount, the command shape is:

```
mount [-t TYPE] [-o OPTIONS] SOURCE TARGET
```

Choose `-o policy=deny-missing`, `-o policy=synth-ephemeral`, or
`-o policy=synth-persist` using [Policy
classes](~peios/mount-policies/policy-classes). `--synth-sddl SDDL` supplies a
well-formed template with an owner, and is valid only with a `synth-*` policy.
Use a verified [stable source name](~peios/disks-and-filesystems/stable-device-names).

`policy=` works only on a new filesystem mount. Bind, move, remount,
propagation and list mode reject it; `mount -o remount` is not a policy-change
interface. The policy is set on the detached filesystem before publication. If
that step fails, no mount with the unintended policy is attached.

After success, list mounts again and confirm the source, target and filesystem.
Use a privileged policy reader to confirm the class and template; the ordinary
mount listing is not a template dump. See the full
[`mount`](~peios/mount-policies/mount) and
[`umount`](~peios/mount-policies/umount) references for flags and status codes.

## kacs_set_mount_policy

This is the administrative interface for changing an existing superblock's
policy. The target fd can refer to an object anywhere on that superblock.
The update replaces the class and template atomically and returns a new
generation; it does not walk the filesystem.

The [kernel administration contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#administration)
explains the operation. The original argument table, validation sequence and
return values are retained in [Mount-policy syscall
notes](~peios/advanced-peios/peios-kernel/kacs/facs/mount-policy-syscalls#kacs-set-mount-policy).

### Privilege requirement

> [!WARNING]
> Published descriptions disagree about the privilege gate. The command and
> SDK pages say `SeTcbPrivilege`; the kernel contract and policy-change event
> reference permit enabled `SeManageVolumePrivilege` or `SeTcbPrivilege`.
> Confirm the contract for the deployed version before planning a change.
> Do not interpret administrator membership alone as proof the call will work.

The older TCB-only description routes ordinary administrators through a
privileged management tool, with peinit and other TCB components applying boot
policy. Disk Manager currently cannot make changes at all; see
[Disk Manager](~peios/disks-and-filesystems/disk-manager).

### The template SD

Choose a template deliberately: it supplies a descriptor when parent inheritance
does not yield one, commonly at the filesystem root. It is a complete
self-relative SD containing owner, primary group, DACL and optional SACL.
Malformed templates are rejected without changing the current policy.

The kernel contract limits it to 65,535 bytes and accepts it only for synthesis;
setting deny-missing clears the template and rejects a non-empty one. Earlier
syscall notes describe a 64 KiB cap and an optional template more generally.
That discrepancy remains unverified. With no usable parent or template,
synthesis uses the [fallback](~peios/mount-policies/policy-classes#the-synthesis-chain).

## kacs_get_mount_policy

A privileged reader uses this interface to retrieve the current class,
generation and, when requested, template. Read it before and after a change;
checking the class alone will miss an unintended template.

The privilege discrepancy above applies to reads too. For fd/argument details,
see [the retained syscall
notes](~peios/advanced-peios/peios-kernel/kacs/facs/mount-policy-syscalls#kacs-get-mount-policy).
The [SDK wrapper](~peios/developing-for-peios/sdk-reference/sdk-files/mount-policy)
has its own documented buffer convention; do not substitute raw-syscall error
handling for that wrapper.

## The generation counter

Every successful policy or template replacement increments a per-superblock
counter. Cached policy-derived state is checked against it and re-derived on
next access if stale. Applying a policy therefore does not require an immediate
scan of every inode. The [kernel reference](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#administration)
covers the cache mechanism.

### What the generation counter affects

Missing-SD and ephemeral-synthesis cache entries, template-derived state, and
pending persistent-synthesis entries are invalidated lazily. Stored SDs and
already-open fds' granted masks are unchanged. Uncached inodes simply use the
current policy on their next access.

### Reading the counter

Compare the value from `kacs_get_mount_policy` with your earlier read to detect
a change. Initial values are implementation-defined, and values from different
superblocks are unrelated. The counter identifies changes, not a wall-clock
change time.

## What happens at a policy change

The class and template are replaced, the generation increments, and future
accesses discard stale policy-derived state. Files with stored SDs keep them;
open handles retain their masks. No file tree is rewritten or reorganised.

## What policy changes do not do

- Switching ephemeral to persistent does not save every cached SD immediately.
  A later access re-synthesises a missing descriptor under the new policy and
  schedules write-back.
- Switching to deny-missing does not provision files you have not visited.
  Any remaining missing SD can cause denial.
- A change does not close handles or revoke their cached rights.
- Other superblocks are unaffected, even when reached beneath this mount.
  Bind paths sharing this superblock are affected.

## Use patterns

| Task | Apply and verify |
|---|---|
| Boot-time policy | peinit applies the configured class and template; the original guide describes registry-based configuration. Verify the resulting mount rather than assuming a configuration was applied. |
| Adopt a non-Peios filesystem | Use persistent synthesis only when you intend to write SDs. Check stored descriptors, including rarely accessed files, before changing to deny-missing. |
| Attach removable media | Use ephemeral synthesis when metadata must remain unchanged. Select read-only separately if file-data writes must also be prevented. |
| Harden an existing deployment | Review templates, move from ephemeral to persistent if adoption is intended, then validate preservation before deny-missing. Each transition is per superblock; it does not convert the tree in one pass. |

## Errors

| Symptom | What to check |
|---|---|
| `-EBADF` from a policy call | The fd must name an object on the intended superblock. |
| `-EPERM` | Check the enabled privilege and deployed-version contract; see the discrepancy above. |
| `-EINVAL` on set | Unknown or `unmanaged` class, reserved fields, malformed/oversized template, or incompatible template input. A rejected change leaves current state unchanged. |
| `-ERANGE` on raw get | The original syscall notes say the required template size is returned for a too-small buffer. The SDK wrapper instead documents success with a length and null template pointer; follow the interface actually used. |
| Denial after a successful policy change | Check whether the SD is missing or corrupt. Corrupt SDs remain denied under synthesis; policy changes do not repair them. |
| Old access still works through an open fd | Existing handles retain their granted masks. Test future access with a new handle. |

Do not use `unmanaged` as a workaround: the public ABI rejects it. StrataFS's
fixed policy also cannot be changed. Read the full error tables in the
[syscall notes](~peios/advanced-peios/peios-kernel/kacs/facs/mount-policy-syscalls#errors)
and the [mount command](~peios/mount-policies/mount#exit-status).

## See also

- [Policy classes](~peios/mount-policies/policy-classes): choose a class and
  diagnose missing or corrupt SDs.
- [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem):
  check whether a descriptor can persist.
- [Privileges](~peios/privileges/overview): understand the privilege gate.
- [File Descriptor Storage](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage):
  kernel policy, caching, write-back and repair contract.

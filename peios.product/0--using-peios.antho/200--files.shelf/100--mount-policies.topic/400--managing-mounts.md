---
title: Managing mounts
type: how-to
description: Inspect live mount policies in Disk Manager, attach a filesystem, check the limits on changing an existing policy, and verify startup mounts.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/disks-and-filesystems/disk-manager
  - peios/privileges/overview
---

Identify the filesystem and inspect its current state before attaching storage
or planning a policy change. Verify both the missing-descriptor class and the
synthesis template. If it is already mounted, read the [change
limits](#before-changing-an-already-mounted-policy) before proceeding.

## Inspect live mounts and policy

Use these read-only listings first:

```sh
lsblk
mount
```

`mount` lists live state from the kernel; Peios has no `/etc/fstab` or
`/etc/mtab`. The listing is limited to mounts your token may observe. An empty
or partial listing does not prove that a device is unused.

Match the intended filesystem to a verified [stable source
name](~peios/disks-and-filesystems/stable-device-names), then check its live
source, target and filesystem type. To inspect its policy in **Disk Manager**:

1. Open the launcher and type `disk`.
2. Select [**Mounts**](~peios/disks-and-filesystems/disk-manager#mounts), then
   the intended mount to see its options and policy.
3. Open **Permissions…** to inspect the synthesis template. The [UI policy
   labels](~peios/disks-and-filesystems/disk-manager#files-without-permissions)
   explain the missing-descriptor choices.

Check both class and template; the ordinary `mount` listing is not a template
dump. If Disk Manager cannot read the policy, verification remains incomplete.
Missing details do not establish the intended policy, and the GUI does not
bypass the privilege gate. See [what Disk Manager may
show](~peios/disks-and-filesystems/disk-manager#what-you-may-see-and-change).

### Check policy access

> [!WARNING]
> In kernel source `8e0e22de3a59cad506bbbf8873de456e16ad272d`, both policy
> reads and writes accept enabled `SeManageVolumePrivilege` or `SeTcbPrivilege`;
> recording the privilege as used must also succeed. Administrator membership
> alone does not satisfy this gate. This is a [pinned source finding](https://github.com/peios/pkm/blob/8e0e22de3a59cad506bbbf8873de456e16ad272d/kacs/capability.c#L613-L637),
> not a test of the kernel deployed on your machine or a historical release boundary.

The `mount` diagnostic in peiosutils 0.8.18 still [names only
`SeTcbPrivilege`](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/mount/src/policy.rs#L84-L99).
That hint is misleading for the pinned kernel. Check the deployed kernel and
caller's effective token before changing privileges; do not automatically grant
TCB or globally remap `CAP_SYS_ADMIN` to make the operation succeed.
`SeManageVolumePrivilege` is narrower than TCB but still permits substantial
[authority over paths and synthesised policy](~peios/privileges/categories#what-semanagevolumeprivilege-is-actually-worth).

## Attach a filesystem

> [!WARNING]
> Ephemeral synthesis avoids writing back synthesised security descriptors;
> it does not guarantee an unchanged disk. Even a read-only ext4 mount can
> replay its journal. If preservation requires no disk writes, use a supported
> inspection procedure for that filesystem. [How the installer's disk scan
> stays read-only](~peios/disks-and-filesystems/installing-to-disk#how-the-disk-scan-stays-read-only)
> explains its additional safeguards; a policy choice alone is not that procedure.

For a new mount, the command shape is:

```
mount [-t TYPE] [-o OPTIONS] SOURCE TARGET
```

Choose `-o policy=deny-missing`, `-o policy=synth-ephemeral`, or
`-o policy=synth-persist` using [Policy
classes](~peios/mount-policies/policy-classes). Use the verified stable source
name and the intended target mount point. Use persistent synthesis only when
writing SDs is intended; select read-only separately if file-data writes must
be prevented.

`--synth-sddl SDDL` supplies a well-formed template with an owner, and is valid
only with a `synth-*` policy. Review the [synthesis chain and
fallback](~peios/mount-policies/policy-classes#the-synthesis-chain) before
exposing the volume: parent inheritance takes precedence, and omitting a
template does not imply private access.

If setting the attach-time policy fails, no mount with the unintended policy
is attached. The [`mount` reference](~peios/mount-policies/mount#kacs-mount-policy)
describes that guarantee and the full option contract.

After success, [inspect the live mount and policy](#inspect-live-mounts-and-policy)
again. Confirm the source, target, filesystem, class and template.

## Before changing an already-mounted policy

`mount` sets policy only for a new filesystem mount. Bind, move, remount,
propagation and list mode reject `policy=`; `mount -o remount` is not a
policy-change interface. Disk Manager cannot commit changes because its
privileged disk service is missing, including changes offered by its forms.

The kernel exposes a privileged interface for an existing filesystem instance
(the superblock), but these operator tools do not provide a ready-to-use
command or working GUI flow for changing its policy. Confirm a supported
privileged integration for the deployed system before proceeding, including
its [policy access requirements](#check-policy-access).

For integration authors, the [kernel administration
contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#administration),
[SDK wrappers](~peios/developing-for-peios/sdk-reference/sdk-files/mount-policy)
and [syscall notes](~peios/advanced-peios/peios-kernel/kacs/facs/mount-policy-syscalls)
cover arguments, template validation, buffer handling, errors and generation
semantics. The privilege disagreement is resolved for the pinned source above;
other differences retained in the syscall notes are not resolved by that finding.
A rejected policy change leaves the current class and template unchanged.

A second mount of the same device does not establish an independent policy
boundary. Read the [`mount` superblock-reuse
restrictions](~peios/mount-policies/mount#other-flags) before relying on a
separate instance; detaching and reattaching is not a generic policy-change
procedure.

### What a policy change affects

- All bind paths sharing the filesystem instance share the new policy.
  Independent superblocks are unaffected, even when reached beneath this mount.
- Stored descriptors remain unchanged. Already-open handles retain their
  granted rights; future access checks use the new policy.
- No file tree is rewritten or provisioned. Changing ephemeral to persistent
  does not save every cached SD immediately; later missing-descriptor accesses
  derive under the new policy and schedule best-effort write-back.
- Deny-missing can leave files without stored SDs inaccessible. Corrupt
  descriptors remain denied under every managed class; synthesis does not
  repair them.

Before hardening an adopted filesystem, check [class
transitions](~peios/mount-policies/policy-classes#class-transitions) and
[validate descriptor
preservation](~peios/mount-policies/sd-storage-by-filesystem#validate-descriptor-preservation),
including rarely accessed files. Persistent synthesis is incremental adoption,
not a whole-tree guarantee; mounted `sd` output alone does not prove durable
storage.

## Mount non-root storage at startup

The root filesystem is mounted by the initramfs before peinit takes over.
A non-root data partition is mounted by an ordinary **Oneshot service**;
peinit does not mount it directly. See [Where peinit takes
over](~peios/services-and-jobs/boot-and-boot-modes#where-peinit-takes-over).

Use [Defining a service](~peios/services-and-jobs/defining-a-service) for the
definition, validation and boot-trigger fields, and [Oneshot
services](~peios/services-and-jobs/service-types#oneshot-services) for the
completion contract. A service using a [stable device
name](~peios/disks-and-filesystems/stable-device-names#who-creates-them) needs a
`Requires` dependency on the device manager so the boot-time device replay
finishes before it opens that name.

These pages establish the service mechanism, but do not yet give a complete
storage-specific recipe: the service identity, required privileges and mount
arguments must be confirmed for the deployed system before creating a
definition. There is no dedicated mount-registry schema established here, and
[Disk Manager](~peios/disks-and-filesystems/disk-manager#at-startup) cannot
currently save startup mounts.

After the service runs, inspect its [status and
logs](~peios/services-and-jobs/defining-a-service#change-and-verify). A successful
Oneshot reports successful command completion and can then return to
**Inactive**; its status alone does not establish the current mount or policy.
Separately [inspect the live mount](#inspect-live-mounts-and-policy), checking
source, target and filesystem, and [read the policy](#inspect-live-mounts-and-policy) to
confirm both class and template.

## Check unexpected results

- **Attachment failed:** read the command's diagnostic and [`mount` exit
  status](~peios/mount-policies/mount#exit-status). Check the source, options and
  reported permission or filesystem failure. A failed attach-time policy step
  does not publish a mount with an unintended policy.
- **Policy details are unavailable:** check [policy
  access](#check-policy-access) and Disk Manager's visibility limits. Do not
  treat an unreadable class or template as successful verification.
- **A file is still denied:** distinguish a [missing descriptor from a corrupt
  one](~peios/mount-policies/policy-classes#corrupt-sd-handling). Deny-missing
  rejects missing SDs, and switching to synthesis does not repair corrupt SDs.
- **Old access still works through an open handle:** existing handles retain
  their granted rights. Check future access using a new handle.

`unmanaged` is reserved for the kernel and cannot be set administratively.
StrataFS's policy is fixed; neither is a workaround for an access failure.

## See also

- [Policy classes](~peios/mount-policies/policy-classes): choose a class and
  diagnose missing or corrupt SDs.
- [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem):
  check whether a descriptor can persist.
- [Privileges](~peios/privileges/overview): understand the privilege gate.
- [File Descriptor Storage](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage):
  kernel policy, caching, write-back and repair contract.
- [`mount`](~peios/mount-policies/mount): attachment options and status codes.
- [`umount`](~peios/mount-policies/umount): detachment options and status codes.

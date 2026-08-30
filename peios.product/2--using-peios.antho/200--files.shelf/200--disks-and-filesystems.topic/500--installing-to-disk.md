---
title: Installing to disk
type: concept
description: How a Peios system is copied from a live medium onto a disk, and how the installed system boots itself afterwards.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/disks-and-filesystems/mke2fs
  - peios/boot-and-trust-establishment/boot-hooks
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/mount-policies/policy-classes
---

A live Peios runs from a read-only squashfs with a tmpfs stacked on top, so every write it accepts is discarded at reboot. Installing to disk replaces that arrangement with a writable filesystem that survives — and, less obviously, replaces a security policy chosen at *mount* time with one the filesystem carries itself.

Installation is five steps and one retirement. Nothing about it is magic, and all of it can be done by hand.

## Two ways to invoke it

```
peios-install --yes --whole-disk /dev/vda      # partition the disk, then install
peios-install --yes /dev/vda1 /dev/vda2        # install onto partitions that exist
```

The first form runs [`part`](~peios/disks-and-filesystems/partitioning) before anything else — a fresh GPT, a 512 MiB ESP, and a root filling the remainder — and then proceeds exactly as the second. **The whole disk is erased.**

If the disk already carries a partition table `part` did not create, the install stops rather than overwriting it; `--force` is how you say you meant it. That refusal happens before the first `mkfs`, so nothing has changed when it does.

The second form is for any layout other than the one above: partition however you like with `part`, then name the two partitions.

## What the installer does

**1. Format the EFI system partition.** UEFI requires FAT, so this is `mkfs.vfat -F 32`. A FAT filesystem cannot hold a security descriptor and never will, so the ESP's access policy comes entirely from its mount — necessarily one of the synthesising classes.

**2. Format the root, with a descriptor.** This is the step with no equivalent on other systems:

```
mke2fs -t ext4 -E root_sddl="O:SYG:SYD:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)(A;OICI;GRGX;;;WD)" /dev/vdb2
```

The descriptor is written to the root directory's `security.peios.sd` at format time, so the filesystem is administrable from the instant it exists. Because every ACE is inheritable, everything created inside it derives its own descriptor from that one.

It is byte-for-byte the descriptor the live system's own root carries, which is the point: an installed system should not quietly have a different access policy from the medium it was installed from. Everyone gets read and execute rather than read alone because on Peios execute is also traverse, and a principal that cannot traverse a directory cannot enter it — which would leave every service that does not run as SYSTEM unable to reach its own working directory. See [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors).

**3. Copy the system.** `cp -ax`, which preserves owner, DACL, SACL, timestamps, links and extended attributes, and stops at filesystem boundaries. Every one of those is required rather than best-effort, so a descriptor that cannot be carried across stops the install instead of quietly downgrading it. Mountpoints are recreated as empty directories rather than copied into: `/proc`, `/sys` and `/dev` are mount-moved into the new root by prelude at boot, and `/bin`, `/etc`, `/lib` and the rest are StrataFS views mounted over theirs. What lives *behind* those views — `/usr` and `/lcl` — is ordinary content on the root filesystem, and is copied in full.

**4. Write the kernel command line.** The installed system needs `root=`, naming the filesystem that did not exist until step 2. That cannot be package data, so it is generated: the `disk-boot` package ships a template at `/usr/share/disk-boot/cmdline` carrying everything stable, and the installer appends `root=UUID=<the new root>` and writes the result to `/lcl/etc/boot/cmdline` on the target. Package data supplies the general part; the operator tree holds the per-install part.

**5. Build the boot artifact.** `mkuki` bundles the kernel, the initramfs and that command line into a single EFI binary, written to the ESP at `EFI/BOOT/BOOTX64.EFI`.

That last path is the removable-media fallback, which UEFI firmware boots without an NVRAM entry. A Peios installation therefore needs **no bootloader and no boot manager** — there is nothing between the firmware and the kernel.

## What it refuses before it starts

Both partitions you name are about to be formatted, so the installer checks them before it does anything irreversible. It stops if either is not a block device, if you name the same partition twice, or — the one worth stating plainly — **if either is currently mounted**:

```
# peios-install --yes /dev/vda1 /dev/vda2
peios-install: /dev/vda2 is mounted; refusing to format it
```

That last check is what stands between you and naming the partition you are running from. All of it happens before the first `mkfs`, so a rejected install has changed nothing.

## The first-account service is retired, the account is not

Your accounts come across. What does not is the thing that *creates* them.

A live image ships `lpsd-first-account`: a oneshot service that runs `lps add` at boot to create the development account. It is written for exactly one situation, which is a live image — the root there is a tmpfs, so every boot starts from an empty store and the provisioner has work to do.

An installed system is the other situation. The accounts themselves live in lpsd's store at `/var/state/lpsd/principals`, which is ordinary content on the root filesystem and is copied like everything else. So the installed machine already has the account before it first boots, and re-running a provisioner against a populated store is not a harmless no-op: the script carries no idempotence guard, so `lps add` fails on the name that already exists and the service crashes on every boot. Once installation grows a "choose a password" step, it would be worse than noisy — a provisioner that reasserts the image's credential would undo the operator's choice at the next reboot.

So before it copies anything, the installer deletes the service from the registry:

```
reg del 'Machine\System\Services\lpsd-first-account'
```

Note *which* registry. It removes the key from the **live** system it is running on, not from the target — the registry is a live database served by `registryd`, and the only thing that can safely edit it is the `registryd` currently holding it open, so the removal happens at the source and the copy never carries it. Running the installer again, or running it from an already-installed system, finds nothing to remove and says so. The removal is checked afterwards and a failure stops the install, which happens before either partition is formatted and therefore costs nothing.

> [!CAUTION]
> One thing this deliberately does not solve: the account arrives with the password it had, and on an image that shipped a development account that password is in the image and therefore public. Until installation can prompt for a new one, treat a freshly installed system as carrying a known credential and change it — `lps` is the tool — before the machine is anywhere it matters.

## Use UUIDs, not device names

Step 4 records the root by UUID, and the reason is worth understanding rather than copying.

The disk that is `/dev/vdb` while you install — second device, behind the install medium — is `/dev/vda` when you boot it with the medium removed. A device name baked into the command line is a name for *where a disk was plugged in*, not for the disk, and it stops being true the moment the arrangement changes.

The initramfs resolves the UUID by probing block devices directly rather than reading `/dev/disk/by-uuid`, because no device manager runs in the initramfs and those directories do not exist there — see [Stable device names](~peios/disks-and-filesystems/stable-device-names).

## How the installed system boots

The initramfs contains **two** hooks that can mount a root, and both are present in every image:

| Hook | Mounts |
|---|---|
| `mount-root.sh` | a live medium's squashfs, with a tmpfs overlay above it |
| `mount-root-disk.sh` | an installed root partition, directly |

Both run at every boot. `root=` on the command line decides which one acts; the other exits successfully having done nothing. [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks) covers the mechanism.

Two differences in what the disk hook does are worth calling out, because they are the point of installing at all.

**It mounts the partition directly — no overlay.** The live path stacks a tmpfs because the layer beneath it is read-only. An installed root is writable, so an overlay would serve only to throw away everything written to it.

**It mounts `policy=deny-missing`, and runs no `seed-sd`.** A live root has no descriptors at all — the squashfs ships none — so the live system mounts it `synth-ephemeral` and has KACS invent one per inode, then seeds a single inheritable descriptor onto the tmpfs above. An installed root needs none of that: it carries a real descriptor, written at format time, so a file *without* one is a fault worth surfacing rather than a gap to paper over.

This is the substantive difference between the two, and it is easy to check on a running installed system:

```
# sd show /
  Owner:      LocalSystem (S-1-5-18)
  DACL: (2 ACEs)
    [0] allow LocalSystem (S-1-5-18)                   0x10000000  [CI,OI]
    [1] allow BUILTIN\Administrators (S-1-5-32-544)    0x10000000  [CI,OI]
```

No `ID` flag on either ACE. `ID` is `INHERITED_ACE`, so its absence means this descriptor is *explicit* — stored on the root inode by `mke2fs`, not derived from an ancestor and not synthesised at mount. The filesystem's access policy is a property of the filesystem.

## What the installer does not do

**It does not choose your partition layout.** `--whole-disk` writes one specific arrangement — a 512 MiB ESP and a root filling everything else — and that is all it will ever write. Anything else is a job for [`part`](~peios/disks-and-filesystems/partitioning) followed by the two-partition form of the installer.

**It does not choose a layout.** One ESP, one root, no separate `/home`, no swap, no encryption. Each of those is a real thing to want and none of them exists yet.

**It does not express a per-directory access policy.** The whole installed tree inherits from that single descriptor on the root. That is a complete answer for a system tree where everything is administrator-owned, and it is not a way to say "readable system tree, private home directories" — one inheritable ACL cannot say two different things. Per-subtree descriptors are the work that makes that expressible.

## Where to go next

For the format-time descriptor and how a populated tree gets its own, read [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors).

For the hook mechanism the two root-mounting hooks share, read [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks).

For what `deny-missing` does with a file that has no descriptor, and why the live path cannot use it, read [Policy classes](~peios/mount-policies/policy-classes).

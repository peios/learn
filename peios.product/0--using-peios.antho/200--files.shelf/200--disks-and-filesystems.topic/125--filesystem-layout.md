---
title: Where files live
type: how-to
description: Find software, local configuration, service state, user data and boot files, and distinguish runtime views from the directories behind them.
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/stratafs/overview
  - peios/disks-and-filesystems/diagnose-storage-pressure
  - peios/registry-concepts/find-a-setting
  - peios/registry-administration/lcs-and-sources
  - peios/file-permissions/managing-file-security
---

Use this map to find files and trace merged paths such as `/bin` and `/etc`
to the directories that actually store their contents.

The map describes the base filesystem in
[`dev.peios.fsbase` at `92b0caf`](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.fsbase/dev.peios.fsbase.package.pekit.toml).
Images and local configuration can differ. Inspect the running machine before
assuming its layout or storage lifetime matches.

## Choose where to look

| What you are looking for | Location and purpose |
|---|---|
| Vendor-supplied software and defaults | `/usr`: executables in `bin`/`sbin`, helpers in `libexec`, libraries/modules/firmware in `lib`, shared files in `share`, defaults in `etc`/`conf`. |
| Local software and file-based overrides | `/lcl`: operator-managed trees such as `bin`, `sbin`, `etc` and `conf`. Local entries can hide vendor entries. |
| Files generated from registry configuration | `/system/retc`: reconciler output projected into `/etc`. Find the owning setting or component before editing its generated output. |
| Service data and identity stores | `/var/state`: persistent mutable state, including reserved `services` and protected `secrets` namespaces. See [registry source paths](~peios/registry-administration/lcs-and-sources#the-base-source-registryd) for the machine's hives. |
| Caches, logs and crash data | `/var/cache`, `/var/log` and `/var/crash`. Check service configuration: recorded events and service output need not be text files here. Start with [Event Viewer](~peios/logs-and-events/event-viewer). |
| A person's files | `/home`: human home directories; services use configured state/runtime directories. Access depends on security descriptors. |
| Operator-managed bulk data | `/data`. Its name does not imply a separate disk or a backup policy. |
| Content served by this host | `/srv`: the host's served-content namespace. Check the service configuration for the actual path. |
| Software with its own directory layout | `/opt`. |
| Runtime sockets and service directories | `/run`, including `/run/services`. Sockets and PID files are runtime resources, not saved service data. |
| Temporary working files | `/tmp` and `/var/tmp`; read the lifetime caveat below. |
| Boot inputs and generated artifacts | `/boot` holds the initramfs source tree and EFI-partition mount location; `/system/boot` holds generated initramfs output. Check that the intended EFI partition is mounted. |
| Additional mounted storage | `/mnt` and `/media` are available mount locations. Their existence does not attach a device. |
| Kernel and device interfaces | `/proc`, `/sys` and `/dev`. These expose runtime interfaces, not ordinary saved application data. |

A path does not grant access or prove that its data is safe to delete, backed
up, or kept during installation. For space problems, use
[Find why a filesystem is full](~peios/disks-and-filesystems/diagnose-storage-pressure)
before deleting anything.

## Trace a runtime path to its real file

The base system uses StrataFS views for `/bin`, `/sbin`, `/lib`, `/libexec`,
`/share`, `/include`, `/etc` and `/conf`. Ordinary views put the corresponding
`/lcl` directory above `/usr`; the vendor stratum is read-only **through that
view**. This does not make the underlying `/usr` tree universally read-only.

Use the read-only inspector:

```sh
stratafs list
stratafs list /etc
stratafs resolve /bin/sh
```

`list` shows the current mount namespace; `resolve` explains providers and write
routing without writing or granting permission. See [Inspecting a stack](~peios/disks-and-filesystems/stratafs/overview#inspecting-a-stack)
for interpretation and access limits.

`/lib64` is different: the reviewed x86-64 base supplies a relative symlink to
`usr/lib/x86_64-linux-peios`, not a StrataFS view. The ordinary `/lib` view maps
the whole `lib` trees, including modules and firmware. These distinctions are
implemented by the
[base recipe](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.fsbase/pekit.toml)
and [root-filesystem hook](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.fsbase/src/mount-rootfs-stratafs-base.sh#L64-L92).

## Find the owner of configuration

Start with [Find where a setting lives](~peios/registry-concepts/find-a-setting)
and the component's `regman` documentation. A visible `/etc` file may be generated
from a registry setting; find that setting rather than changing generated output.

In the reviewed real-root hook, `/etc` has this precedence:

1. `/system/retc`: generated registry output.
2. `/lcl/etc`: local configuration, also the create stratum.
3. `/usr/etc`: vendor defaults.

An existing generated name wins over the same name in `/lcl/etc`. `/conf` has
only local and vendor tiers. The
[initramfs hook](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.fsbase/src/mount-initramfs-stratafs-base.sh#L66-L84)
also uses only local and vendor tiers for `/etc`; do not assume the installed
root and the startup environment have identical views.

> [!NOTE]
> These current-source `/etc` and `/lib64` descriptions differ from the
> [install-destination specification](~peios/advanced-peios/pspu/package-format-and-repository-protocol/install-destinations).
> Check the deployed view before choosing an override location.

`/lcl/policy` is separate from ordinary file-based configuration. Its autorun
and registry-apply directories carry boot policy, not general-purpose storage;
see [peinit’s Phase 1 reference](~peios/peinit/boot/phase-1)
for their authority and execution rules.

## Check temporary-file and boot-storage assumptions

In the reviewed base setup, `/tmp` is a plain directory. The fsbase package's
[temporary-directory policy](https://github.com/peios/pkgs/blob/92b0caf88e87c72931eee188a07ac87883d913c7/dev.peios.fsbase/dev.peios.fsbase.package.pekit.toml)
explains that it is disk-backed on an installed system and is not cleared at
boot or size-limited by that setup. A live image's volatile upper layer has a
different lifetime. Do not rely on a reboot to erase temporary files, or assume
that `/tmp` has a separate space budget. `/var/tmp` is intended for temporary
files that survive reboot; check the actual mount and local cleanup policy.

For boot files, the [activation checklist](~peios/peiso/editions-and-upgrades/upgrading-peios#check-what-an-update-has-activated)
distinguishes generated output, the intended EFI partition and the running kernel.

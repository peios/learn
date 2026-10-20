---
title: Filesystem Layout
type: reference
description: Locate software, configuration, state, and boot files while distinguishing runtime views from backing storage.
---

The base layout separates packaged files, local overrides, generated output,
and mutable state. Images and local mounts can differ. A path alone does not
prove persistence, a separate storage budget, a backup policy, or permission
to remove its contents.

| Location | Purpose |
|---|---|
| `/usr` | Packaged executables, libraries, helpers, shared files, and defaults. |
| `/lcl` | Operator-managed software and file-based overrides. |
| `/system/retc` | Generated configuration projected into the runtime `/etc` view. |
| `/var/state` | Persistent service and identity state, including protected secrets. |
| `/var/cache`, `/var/log`, `/var/crash` | Component-managed caches and diagnostic data; event records need not be text files here. |
| `/home` | Human home directories. Services use their configured state paths. |
| `/data`, `/srv`, `/opt` | Bulk data, served content, and software with its own layout. |
| `/run` | Runtime sockets, service directories, and locks. |
| `/tmp`, `/var/tmp` | Temporary work; check the actual mount and cleanup policy. |
| `/boot`, `/system/boot` | Boot inputs, the EFI mount, and generated boot artifacts. |
| `/mnt`, `/media` | Mount locations; creating a directory does not attach storage. |
| `/proc`, `/sys`, `/dev` | Kernel and device interfaces. |

## Follow the runtime view

The conventional `/bin`, `/sbin`, `/lib`, `/libexec`, `/share`, `/include`,
and `/conf` views place local directories above vendor directories. The
real-root `/etc` view additionally puts `/system/retc` above `/lcl/etc` and
`/usr/etc`. An existing generated name can therefore hide a local override.
Find the owning registry setting before editing generated output.

The `+ro` flag protects a stratum through that view; it does not make direct
access to the backing `/usr` path universally read-only. On the reviewed
x86-64 base, `/lib64` is a relative link to `usr/lib/x86_64-linux-peios`, not
a
StrataFS mount. The `/lib` view still covers modules and firmware. Temporary
boot views can differ from real-root views.

Use [StrataFS inspection](~peios/peiosutils/disks-and-mounts/inspecting-stratafs)
to identify the actual provider before changing a file. Removing a local
override can reveal a vendor file; it does not create a whiteout.

## Default policy is not a live inventory

The retained fsbase recipe supplies these policy intentions. Later package,
service, installer, or administrator changes can narrow them further.
Inspect the deployed descriptors rather than assuming a path proves access.

| Scope | Intended baseline |
|---|---|
| Public software and selected local configuration trees | SYSTEM and Administrators manage; other users receive read/traverse access where specified. |
| `/var/state`, caches, logs, crash data, `/data`, and `/srv` | Administrative control with traversal where specified; no universal read grant to service contents. |
| `/home` | Traversal without a general directory-list grant; each home supplies its own policy. |
| `/tmp` and `/var/tmp` | Shared creation with creator-specific child policy, not inherited public access to every temporary file. |
| `/var/state/secrets` | SYSTEM-only baseline. |
| Identity stores | The owning service and SYSTEM; for example, lpsd's credential store has its own narrower policy. |

These are not interchangeable repair templates. In particular, applying a
public system-tree descriptor recursively to private state exposes data.
`/lcl/policy` holds privileged boot policy and is not ordinary override
storage.

The retained installed layout uses a disk-backed `/tmp` without automatic
boot clearing in fsbase. A live image's volatile layer has a different
lifetime. Check actual cleanup and mount configuration before relying on
reboot to erase a file. Check which EFI filesystem is mounted before replacing
boot artifacts; generating an image elsewhere does not activate it.

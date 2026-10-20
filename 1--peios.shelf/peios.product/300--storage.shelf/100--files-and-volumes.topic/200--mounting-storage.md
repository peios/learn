---
title: Mounting Storage
type: how-to
description: Choose missing-descriptor behavior, verify the filesystem instance, and distinguish attachment from policy conversion.
---

Inspect the device, existing mounts, and intended target before attaching
storage. Use `lsblk`, `part list`, and `mount`, retaining diagnostics
alongside
the listings. Limited visibility does not prove a disk is unused.

## Choose the missing-descriptor behavior

| Policy | Purpose |
|---|---|
| Deny missing | Use provisioned storage with valid stored descriptors. |
| Ephemeral synthesis | Derive missing descriptors without saving those derived values. |
| Persistent synthesis | Adopt missing descriptors incrementally through deferred write-back. |

A valid stored descriptor remains authoritative. A corrupt one is refused
rather than replaced through synthesis. Unmanaged policy is reserved for
kernel-owned cases; it is not an administrative way to disable file security.
StrataFS has a fixed policy.

Synthesis considers parent inheritance, then the mount template, then the
kernel fallback. Omitting a template does not mean private access. Persistent
synthesis is not a whole-tree conversion, and a readable cached descriptor
does not prove it reached storage. Before moving to deny-missing, verify the
stored descriptors of rarely used files as well as ordinary working files.

The [kernel mount reference](~kernel/internals/kacs/file-security/mount-classes-and-bootstrap-descriptors)
owns defaults and administration, while
[descriptor storage](~kernel/internals/kacs/file-security/descriptor-storage-and-caching)
owns synthesis, corruption, deferred write-back, and repair. tmpfs, devtmpfs,
and boot images do not all default to ephemeral synthesis.

## Verify the attachment boundary

Policy belongs to the superblock, not the mountpoint. Bind paths can share it;
a second mount of the same device need not create an independent policy.
A policy change neither rewrites stored descriptors nor revokes cached rights
on existing handles. Other filesystems mounted below it remain separate.

`mount(1)` documents attach-time policy and template options. Policy is set on
the detached mount before attachment, so failure at that step does not expose
a mount with unintended policy. Other setup can still have happened before a
later failure. A nonzero status is not proof that no state changed.

Remount and bind operations are not policy-change interfaces. Disk Manager's
inspection does not make its unimplemented privileged commit workflow usable.
Changing policy on an existing instance requires a supported integration with
the kernel API. The narrower volume-management privilege can satisfy that
API's gate; do not add TCB merely because a command diagnostic names it.

Read-only mounting and ephemeral synthesis are separate choices. An ext
filesystem can replay its journal even on a read-only mount. For preservation,
use an inspection method that also prevents journal and device writes, such
as the installer's documented read-only loop and `noload` procedure.

After attachment, verify source, target, filesystem, writable state, policy,
and template. Missing policy details leave verification incomplete. Reopen
files when checking a changed policy instead of testing through old handles.

## Arrange startup deliberately

Prelude's hooks mount the root before Peinit. Additional storage can use a
service with an explicit identity, privileges, dependencies, and failure
policy. A service using device-manager links must wait for those links, and
must still handle later device removal.

Define repeat-start and partial-failure behavior. A successful Oneshot service
can become inactive while its mount remains attached; service state is not
live mount state. Do not use an option that lacks an existing-mount guard as
proof of idempotence. Verify both the service result and the mount itself.

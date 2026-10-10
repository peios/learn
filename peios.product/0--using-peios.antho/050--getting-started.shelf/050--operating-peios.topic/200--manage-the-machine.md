---
title: Manage the machine
type: how-to
description: Choose the desktop app or command-line guide for accounts, software, services, networking, storage and machine configuration.
related:
  - peios/operating-peios/overview
  - peios/operating-peios/troubleshoot-a-problem
  - peios/logs-and-events/event-viewer
  - peios/registry-administration/regman
---

Choose the task below. The linked guides explain the controls, required
permissions and how to check the result. Use the machine-wide settings
only when you intend to affect everyone who uses the machine.

## Accounts and desktop settings

[Manage local accounts and groups](~peios/managing-local-principals/overview)
collects the account tasks and access precautions in one place.

- **Create an account or change local membership:**
  [Principals Manager](~peios/managing-local-principals/principals-manager)
  on the desktop, or [Creating accounts](~peios/managing-local-principals/creating-accounts)
  and the [`lps` reference](~peios/managing-local-principals/lps-command)
  in a terminal.
- **Sign in remotely from a terminal or manage SSH keys:**
  [Signing in over SSH](~peios/signing-in/signing-in-over-ssh).
- **Change your own password:**
  [The `passwd` command](~peios/signing-in/the-passwd-command).
- **Change your own desktop:**
  [Desktop Settings](~peios/desktop-settings/overview).
- **Set defaults for everyone or change how the desktop is served:**
  [Settings for all users](~peios/desktop-settings/for-all-users).
  Changing the listen address can disconnect open desktops; an overlay
  prevents normal sign-in while it is set.

## Software

- **Find, install or remove a package:**
  [Package Manager](~peios/package-management/package-manager) on the
  desktop, or [Installing and removing packages](~peios/package-management/installing-and-removing)
  in a terminal. Review the plan, including dependencies, before applying it.
- **Update or undo a package change:**
  [Keeping a system current](~peios/package-management/keeping-a-system-current).
- **Set up or enable a feature delivered by a package:**
  [Feature Manager](~peios/features/feature-manager). Installing a package
  puts files in place; feature setup is a separate action.
  [Remove a feature before its package](~peios/features/overview#when-its-package-is-removed),
  while the scripts needed to undo its setup are still available.
- **Handle an interrupted package operation:**
  [Transactions and recovery](~peios/package-management/transactions-and-recovery).
  Feature operations have their own [interrupted-state guidance](~peios/features/overview#interrupted).

## Services and running programs

- **Inspect, start, stop or restart a service:**
  [Controlling services](~peios/services-and-jobs/controlling-services).
- **See running programs, resource use and jobs:**
  [Task Manager](~peios/threads-and-processes/task-manager).
- **Read a service's output:**
  [Event Viewer](~peios/logs-and-events/event-viewer) or
  [Service output and logging](~peios/services-and-jobs/output-and-logging).
- **Shut down or reboot:**
  [Shutdown](~peios/services-and-jobs/shutdown).

## Network, time and storage

- **Inspect connections or change network settings:**
  [Network Manager](~peios/networking/network-manager), or
  [The `net` command](~peios/networking/the-net-command) to inspect state
  and [Configuring profiles](~peios/networking/configuring-profiles) to
  change configuration. Read the confirmation and rollback behavior before
  changing the network through a remote desktop.
- **Set the time zone or clock:**
  [Time zone and setting the clock](~peios/time/time-zone-and-setting-the-clock).
- **Inspect disks and filesystems:**
  [Disk Manager](~peios/disks-and-filesystems/disk-manager) is read-only.
  For changes, follow [Managing mounts](~peios/mount-policies/managing-mounts),
  [Partitioning](~peios/disks-and-filesystems/partitioning) or
  [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors).
  Partitioning and formatting can destroy data; follow the warnings in
  those guides before making changes.

## Configuration beyond the settings apps

Use [Registry Editor](~peios/registry-administration/registry-editor) or
[`reg`](~peios/registry-administration/reg) for settings that require a
registry change. Consult [`regman`](~peios/registry-administration/regman)
first: it explains what a key means, accepted values and when changes
apply. A value being stored does not by itself prove the service accepted it.

For configuration backup and recovery, read
[Backup and restore](~peios/registry-administration/backup-and-restore)
before changing the registry's stores or layers.

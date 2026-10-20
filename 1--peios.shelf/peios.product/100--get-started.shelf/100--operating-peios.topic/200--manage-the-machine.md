---
title: Managing the Machine
type: concept
description: Choose the maintained guide for accounts, software, services, networking, and configuration.
related:
  - peios/operating-peios/overview
  - peios/operating-peios/troubleshoot-a-problem
---

Choose the component responsible for the change. Keep a working access route
when changing authentication, the network, or the service that provides your
session. A stored setting is not proof that its consumer accepted it.

## Accounts and desktop

| Task | Guide |
|---|---|
| Create an account or change membership | [Local Accounts](~peios/local-accounts/overview) or [Principals Manager](~peios/local-accounts/principals-manager) |
| Change your password, keys, or display name | [My Settings](~peios/local-accounts/my-settings) or [`passwd`](~peios/local-accounts/passwd) |
| Set token privileges and integrity | [Granting Access](~peios/authentication/granting-access) |
| Connect through SSH | [Signing in over SSH](~peios/signing-in/signing-in-over-ssh) |
| Change personal desktop preferences | [Desktop Settings](~peios/desktop-settings/overview) |
| Change desktop defaults for everyone | [Settings for All Users](~peios/desktop-settings/for-all-users) |

Changing credentials or groups does not rewrite tokens already issued. Keep a
verified administrator route while changing access, and test a fresh sign-in
before closing it. Changing the desktop listener can disconnect users; an
overlay can replace the ordinary sign-in screen.

## Software and services

Use [Package Manager](~peios/packages/package-manager) to inspect and
request package changes. Review dependencies and removals before applying the
plan. [Upgrade Peios](~peios/packages/upgrade-peios) has its own update
workflow and completion checks.

Package installation and feature setup are separate operations. Follow
[Feature Manager](~peios/features/feature-manager) for feature
lifecycle actions. Remove a feature while the package supplying its cleanup
scripts is still installed. An interrupted operation needs the responsible
tool's recovery procedure before another attempt.

For running software:

- Use [Controlling Services](~peios/services-and-jobs/controlling-services)
  for service actions and [service
  output](~peios/services-and-jobs/output-and-logging) for diagnostics.
- Use [Task Manager](~peios/processes/task-manager) to inspect running
  programs, resource use, and sessions.
- Follow [Shutdown](~peios/boot/shutdown) for an orderly
  shutdown or restart.

## Network, time, and storage

[Network Manager](~peios/network-configuration/network-manager) and
[`net`](~peios/network-configuration/the-net-command) show link and configuration state.
Follow [Changing Network
Settings](~peios/network-configuration/changing-network-settings) for confirmation and
rollback when editing a connection remotely. For persistent configuration,
use the managed profiles; manual interface edits can be replaced by netd.

For clock and time-zone problems, use [Keeping the
Time](~peios/time/overview). A wrong display time zone and a clock that is
not synchronized require different corrections.

[Disk Manager](~peios/files-and-volumes/disk-manager) inspects storage; it does not
partition, format, mount, or repair it. For a mount operation, consult
[`mount`](~peios/files-and-volumes/mount) and the filesystem's requirements.
Use the installer or the appropriate storage tool for destructive changes,
after identifying the device and preserving its data.

## Registry configuration

Read the setting's registry manual with
[`regman`](~peios/registry/regman) before editing it. Check its type,
layer, access policy, default, and application timing.

[Registry Editor](~peios/registry/registry-editor) and
[`reg`](~peios/registry/reg) change registry state. After saving, verify
the consuming service or a fresh session as the manual requires. A successful
write does not prove that a service parsed or applied the value.

If local registry storage fails, follow
[Diagnosing Registry Storage
Failures](~peios/registry/diagnosing-failures) before replacing stores
or changing layers.

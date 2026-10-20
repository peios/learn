---
title: Finding Your Way
type: concept
description: Which guide to open for installing Peios, signing in, everyday desktop work, and each administration task, and which reference owns each kind of fact.
related:
  - peios/introduction/what-is-peios
  - peios/introduction/troubleshoot-a-problem
  - peios/signing-in/overview
---

Each task on a Peios machine belongs to the component that owns it, and each
component documents its own tasks. This page sends you to the right guide.
Before you change authentication, the network, or the service that provides
your session, keep a second way in: a console, or another signed-in session.
That way a mistake can't lock you out.

## Installing and first use

To install Peios, prepare a boot medium with
[Preparing a PC](~peios/installing-peios/preparing-a-pc), then follow
[Installing to Disk](~peios/installing-peios/installing-to-disk). Installing
erases the disk you choose, so identify it and save anything you need first.

On a machine with first-boot setup,
[Completing Setup](~peios/first-boot/completing-setup) sets the machine's name
and creates the first administrator. Then continue with
[Signing In](~peios/signing-in/overview). In a browser, check the machine's
certificate before you enter your password.

## Everyday work

The [desktop applications](~peios/everyday-apps/essential-apps) cover files,
text editing, terminals, and system tools.
[Desktop Settings](~peios/desktop-settings/overview) changes your desktop's
appearance and preferences. A tool can't give you permission you don't have:
it acts with your access token, and a machine-wide change affects every user.

## Accounts and security

| Task | Guide |
|---|---|
| Create an account or change membership | [Local Accounts](~peios/local-accounts/overview) or [Managing Accounts in Principals Manager](~peios/local-accounts/managing-local-accounts) |
| Change your own password, keys, or display name | [Changing Your Account Settings](~peios/local-accounts/my-settings) or [Changing Your Password](~peios/local-accounts/passwd) |
| Change the privileges and integrity level that sign-ins receive | [Granting Access](~peios/authentication/granting-access) |
| Find out why access was refused | [Diagnosing an Access Refusal](~peios/identity-and-access/diagnosing-access) |
| Trust or distrust a certificate | [The Trust Store](~peios/certificate-trust/overview) |

Changing an account doesn't change the tokens of programs already running.
Test a fresh sign-in before you close the session you made the change from.

## Software and services

| Task | Guide |
|---|---|
| Install, remove, or upgrade software | [Managing Packages](~peios/packages/package-manager) and [Upgrading Peios from the Desktop](~peios/packages/upgrade-peios) |
| Turn a feature on or off | [Managing Features in Feature Manager](~peios/features/feature-manager) or [from the command line](~peios/features/managing-features) |
| Start, stop, or inspect a service | [Controlling Services](~peios/services-and-jobs/controlling-services) |
| Read a service's output | [Finding Service Logs](~peios/services-and-jobs/output-and-logging) |
| See what is running and what it uses | [Inspecting Tasks and Sessions](~peios/processes/task-manager) |
| Shut down or reboot | [Shutting Down and Rebooting](~peios/boot/shutdown) |

Installing a package and setting up its feature are separate steps. Remove a
feature while the package that supplies its cleanup is still installed.

## Network, time, and storage

| Task | Guide |
|---|---|
| Configure a network connection | [Configuring Profiles](~peios/network-configuration/configuring-profiles) or [Changing Network Settings in Network Manager](~peios/network-configuration/changing-network-settings) |
| Diagnose a connection | [Checking Connectivity](~peios/network-configuration/checking-connectivity) |
| Set the clock or the time zone | [Keeping the Time](~peios/time/overview) |
| Inspect disks and file systems | [Disk Manager](~peios/files-and-volumes/disk-manager) and [Filesystem Layout](~peios/files-and-volumes/filesystem-layout) |

When you change a network connection remotely, use a method that rolls the
change back if you lose contact. Disk Manager inspects storage but doesn't
change it.

## Configuration

Most settings live in the [registry](~peios/registry/the-registry). Before you
change a setting, read its manual with [`regman`](~peios/registry/regman): it
gives the type, valid values, and when a change takes effect. Then change it
with [`reg`](~peios/registry/reg) or [Registry Editor](~peios/registry/registry-editor),
and check that the component using the setting picked it up.

## Reference

Learn explains and links. The facts themselves live in reference forms that
ship with the system:

- **Commands, files, and functions:** the man pages, read with `man`.
- **Registry settings:** the registry manuals, read with `regman`.
- **Events:** the event manuals, read with `evman`, and the
  [events index](~peios/reference/events).
- **How a component works inside:** its technical reference manual, under
  [Reference](~peios/reference).

If something fails, start with
[Troubleshooting a Problem](~peios/introduction/troubleshoot-a-problem) before
you repeat a change or restart a service.

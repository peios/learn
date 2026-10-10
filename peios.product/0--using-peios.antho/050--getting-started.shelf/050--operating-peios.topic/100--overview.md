---
title: Operate a Peios machine
type: how-to
description: Start with the task you need to do — install Peios, complete first boot, sign in, manage the machine or investigate a problem.
related:
  - peios/installing-peios/on-a-pc
  - peios/disks-and-filesystems/first-boot-setup
  - peios/signing-in-from-a-browser/open-the-desktop
  - peios/operating-peios/manage-the-machine
  - peios/operating-peios/troubleshoot-a-problem
---

Use this guide to get a Peios machine running and look after it. You can
use the desktop in a browser or the command-line tools on the machine.
Start with the task you have now; you do not need to read the kernel or
protocol manuals first.

## Install and sign in

1. **Install Peios.** [Install on a PC](~peios/installing-peios/on-a-pc)
   covers the live medium, connecting to the installer and choosing a
   destination disk. Read the disk-erasure warning before continuing.
2. **Complete first boot.** [First-boot setup](~peios/disks-and-filesystems/first-boot-setup)
   sets the machine's identity, network and initial administrator account
   after an installation through the graphical or text installer.
3. **Open the desktop.** [Sign in from a browser](~peios/signing-in-from-a-browser/open-the-desktop)
   explains how to reach the machine and check its certificate before
   entering credentials.

For manual disk preparation and the legacy `peios-install` script, use
[Installing to disk](~peios/disks-and-filesystems/installing-to-disk).
That route has different account and first-boot behavior; follow the
instructions for the installer you actually used.

For a local console or SSH session, see [Sign in](~peios/signing-in/overview).

## Do everyday work

- [Manage the machine](~peios/operating-peios/manage-the-machine): accounts,
  software, services, networking, storage and configuration.
- [Set up your desktop](~peios/desktop-settings/overview): wallpaper,
  clock, dock, shortcuts and default applications.
- [Troubleshoot a problem](~peios/operating-peios/troubleshoot-a-problem):
  find the relevant state and records before changing anything.

## Understand permissions when you need them

Peios tools act with the authority of the account running them. A desktop
app does not grant extra rights simply because it offers a button.
Machine-wide settings are commonly restricted to Administrators; the
individual task guides say what access is needed.

If an action is denied, start with the task's permissions section. Use
[Security fundamentals](~peios/security-fundamentals) when you need to
understand identities, privileges and access rules in more detail.

## Find technical documentation

- [Peios technical reference](~peios/advanced-peios) contains technical reference
  manuals, specifications and implementation reference.
- [Developing for Peios](~peios/developing-for-peios) covers building and
  shipping software, the SDK and developer tools.

The event and command references remain available from Using Peios for
looking up an event you have seen or a command you are about to run.

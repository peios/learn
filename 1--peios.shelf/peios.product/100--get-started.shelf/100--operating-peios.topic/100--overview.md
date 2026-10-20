---
title: Operating Peios
type: concept
description: Find the installation, sign-in, everyday work, and administration guides for a Peios machine.
related:
  - peios/signing-in/overview
  - peios/operating-peios/manage-the-machine
  - peios/operating-peios/troubleshoot-a-problem
---

Peios can provide a desktop in a browser, local consoles, and remote shell
access. Start with the task you need to complete. The component guides explain
its controls, required access, and checks.

## Installation and first use

Use [Installer Interfaces](~peios/installing-peios/interfaces) to choose the
installer available in your image, then follow [Installing to
Disk](~peios/installing-peios/installing-to-disk). Installing over an existing
disk can destroy its contents; identify the destination and preserve needed
data before proceeding.

On an image with first-boot setup, [Completing
Setup](~peios/first-boot/completing-setup) establishes the machine settings
and initial administrator. A custom image needs its own deliberate
[first-account provisioning
route](~peios/local-accounts/creating-an-account#the-first-account).

Continue with [Signing In](~peios/signing-in/overview). Check the
machine's certificate before entering credentials in a browser.

## Everyday work

The [desktop applications](~peios/everyday-apps/essential-apps) cover files,
text editing, terminals, and system tools. [Desktop
Settings](~peios/desktop-settings/overview) controls your shell's appearance
and preferences.

[Managing the Machine](~peios/operating-peios/manage-the-machine) connects
administration tasks to the responsible tools. If something fails, start with
[Troubleshooting a Problem](~peios/operating-peios/troubleshoot-a-problem)
before repeating a change or restarting services.

A graphical control does not grant the permission needed to use it. Tools act
with the caller's token, and machine-wide changes can affect every user.
Follow each task's access prerequisites.

## Reference and development

Use `man` for command interfaces, `regman` for registry settings, and `evman`
for event definitions. These references describe the installed interfaces;
a guide explains how to use them for a task.

For applications, start with the [Peios
SDK](~peios/sdk-basics/what-is-the-peios-sdk). The Kernel product describes
kernel implementation and native interfaces. The Peios Specifications product
contains the shared contracts; neither needs to be read before ordinary
administration tasks.

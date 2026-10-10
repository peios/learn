---
title: Sign in from a browser
type: how-to
description: Reach the GXWI desktop over HTTPS, verify the machine's certificate, and sign in with an account on that machine.
related:
  - peios/signing-in-from-a-browser/the-certificate
  - peios/disks-and-filesystems/first-boot-setup
  - peios/desktop-settings/overview
  - peios/desktop-settings/for-all-users
  - peios/operating-peios/troubleshoot-a-problem
---

The Peios desktop runs on the Peios machine and is displayed in your
browser. To open it, you need the machine's address, the port it is
configured to listen on, and an account on that machine.

If you have just installed Peios with the graphical or text installer,
complete [First-boot setup](~peios/disks-and-filesystems/first-boot-setup)
first. On a live installation medium, follow
[Install on a PC](~peios/installing-peios/on-a-pc) instead: the installer
and its temporary account are different from a normal sign-in.

## 1. Open the machine's address

Open `https://<machine-address>:7780`, replacing `<machine-address>`
with the machine's address or name. Use the configured port if an
administrator changed it.

The desktop service, GXWI, serves HTTPS only. An HTTP request is
redirected to HTTPS; it does not serve an unencrypted desktop.

> [!NOTE]
> The listen setting's built-in default is `127.0.0.1:7780`, which is
> reachable only from the Peios machine itself. An image or administrator
> must configure a reachable address before another device can connect.
> See [Settings for all users](~peios/desktop-settings/for-all-users#advanced).
> Do not change the listen address casually: changing it can disconnect
> open desktops when GXWI next starts.

## 2. Verify the certificate before entering credentials

Each machine creates its own certificate. A browser does not initially
know whether to trust it, so a warning on first use is expected.

Follow [The machine's certificate](~peios/signing-in-from-a-browser/the-certificate)
to compare the browser's SHA-256 fingerprint with the fingerprint shown
at the machine's own console. Do not use a page received over the
connection you are trying to verify as the source of that fingerprint.
If the fingerprints differ, do not sign in.

That guide also explains importing the certificate, name mismatches,
renewal and why a live medium presents a new certificate after each boot.

## 3. Sign in and choose your task

Sign in with an account on this machine. The desktop and its tools use
that account's authority; machine-wide changes may require an
administrator account or specifically delegated access.

- [Desktop Settings](~peios/desktop-settings/overview) changes your
  wallpaper, clock, dock, shortcuts and default applications.
- [Manage the machine](~peios/operating-peios/manage-the-machine) points
  to software, services, accounts, networking and storage tasks.
- [Troubleshoot a problem](~peios/operating-peios/troubleshoot-a-problem)
  covers reachability, refused sign-in and missing records.

If the machine shows an installation or setup overlay instead of a
sign-in screen, follow that flow's guide. While an overlay is configured,
normal sign-in and desktops are unavailable.

## GXWI replaces Atrium

GXWI completely replaces Atrium. Use the HTTPS connection and certificate
verification steps above; the old Atrium connection and application
instructions are retired.

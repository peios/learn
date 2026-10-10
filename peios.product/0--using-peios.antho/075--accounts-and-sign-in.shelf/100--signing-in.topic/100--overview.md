---
title: Sign in
type: how-to
description: Choose a browser, local console or SSH sign-in route, change your own password, and find help when access fails.
related:
  - peios/signing-in-from-a-browser/open-the-desktop
  - peios/signing-in/the-login-command
  - peios/signing-in/the-passwd-command
  - peios/signing-in/signing-in-over-ssh
  - peios/managing-local-principals/overview
  - peios/authentication/overview
---

Choose the sign-in route available on your machine. If you have just installed
Peios, complete [first-boot setup](~peios/disks-and-filesystems/first-boot-setup)
first. Manual and legacy installation routes can provision accounts differently;
[Creating accounts](~peios/managing-local-principals/creating-accounts#where-the-first-account-comes-from)
explains those distinctions.

## Choose how to connect

- **Use the desktop in a browser:** [Open the desktop](~peios/signing-in-from-a-browser/open-the-desktop).
  Check the machine's [certificate](~peios/signing-in-from-a-browser/the-certificate)
  before entering credentials.
- **Use a local console:** [The login command](~peios/signing-in/the-login-command)
  explains the prompt, live-medium autologon and multiple-console behavior.
  Switching consoles does not lock or log out the session you leave.
- **Use a remote terminal:** [Sign in over SSH](~peios/signing-in/signing-in-over-ssh).
  Verify the host fingerprint and read the access precautions before changing
  the SSH service or credential policy.

## Manage your own credentials

Use [passwd](~peios/signing-in/the-passwd-command) to change your own password.
For your SSH keys, follow [Changing your own keys](~peios/managing-local-principals/lps-command#changing-your-own-keys).
Changing another account's credentials is an administration task; start with
[Manage local accounts and groups](~peios/managing-local-principals/overview).

A stored password and the account's credential policy are separate. Follow
[Creating accounts](~peios/managing-local-principals/creating-accounts) when
changing whether a password or SSH key is required; setting a password alone
does not change a passwordless account's policy.

## If sign-in fails

Start with [Troubleshoot a problem](~peios/operating-peios/troubleshoot-a-problem#sign-in-is-refused).
Keep a working administrator route available while investigating. Do not delete
the local principal store to try to restore access: it holds the machine's
identity, and a corrupt store is different from a missing one. See
[The local store](~peios/authentication/the-local-store#missing-versus-corrupt).

For the model behind the prompts, read [How authentication works](~peios/authentication/overview)
and [Logon sessions](~peios/logon-sessions/overview) in Security Fundamentals.

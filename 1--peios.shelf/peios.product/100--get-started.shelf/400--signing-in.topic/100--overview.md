---
title: Signing In
type: concept
description: Choose a browser, console, or SSH route and find the account settings for it.
related:
  - peios/local-accounts/overview
  - peios/operating-peios/troubleshoot-a-problem
---

Use a sign-in route enabled by the machine's image and configuration. On an
installed image with setup enabled, complete [first-boot
setup](~peios/first-boot/completing-setup) first. A custom image needs a
[first-account provisioning
route](~peios/local-accounts/creating-an-account#the-first-account).

## Choose a client

| Connection | Guide | Check before entering credentials |
|---|---|---|
| Browser desktop | [Signing in from a Browser](~peios/signing-in/open-the-desktop) | Verify the machine's certificate fingerprint through a trusted route |
| Local console | [Using a Console](~peios/signing-in/using-a-console) | Use the managed console on the intended machine |
| Remote terminal | [Signing in with SSH](~peios/signing-in/signing-in-over-ssh) | Verify the SSH host fingerprint |

Switching virtual consoles does not lock or end the session left behind.
Rejoining a browser desktop can return to its existing session rather than
create a new one.

## Change your own account

Use [My Settings](~peios/local-accounts/my-settings) for your display name,
password, and SSH keys, or [`passwd`](~peios/local-accounts/passwd)
from a terminal. Self-service credential changes require the proof accepted
by the principal source; a session token alone does not replace that proof.

Changing another account is an administrative operation. Start with
[Local Accounts](~peios/local-accounts/overview) or [Principals
Manager](~peios/local-accounts/principals-manager).

A stored password and credential policy are separate. Setting a password does
not stop credential-free sign-in until the account's policy requires it.
Follow [Managing Credentials](~peios/local-accounts/managing-credentials),
then verify a fresh sign-in before closing the working session.

## Recover from a refusal

Follow [Diagnosing Authentication](~peios/authentication/diagnosing)
and preserve a working administrator route. Do not delete the local store to
clear an error: it holds account identities, and an unreadable store is not an
unprovisioned machine.

For the model behind the prompt, read [Authentication
Conversations](~peios/authentication-client/conversations) and [Sessions and
Account Changes](~peios/local-accounts/sessions-and-account-changes).

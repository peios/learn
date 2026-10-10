---
title: Manage local accounts and groups
type: how-to
description: Create and maintain local users and groups, choose credential policy, and inspect the privileges assigned by this machine.
related:
  - peios/managing-local-principals/principals-manager
  - peios/managing-local-principals/creating-accounts
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/assigning-privileges
  - peios/signing-in/overview
  - peios/authentication/principal-sources
---

Local accounts and groups are held by `lpsd`, the local principal source.
Use [Principals Manager](~peios/managing-local-principals/principals-manager)
on the desktop or the [lps command](~peios/managing-local-principals/lps-command)
in a terminal to manage them. The guides distinguish changes you can make to
your own account from administrator operations.

## Choose a task

- **Create an account:** [Creating accounts](~peios/managing-local-principals/creating-accounts)
  covers credentials, membership and the different first-account provisioning
  routes. The desktop equivalent is [Making a user](~peios/managing-local-principals/principals-manager#making-a-user).
- **Change an account or its sign-in policy:** [Changing a user](~peios/managing-local-principals/principals-manager#changing-a-user)
  or the [lps reference](~peios/managing-local-principals/lps-command).
  A password being set does not by itself require that password at sign-in.
- **Create a group or change membership:** [Groups in Principals Manager](~peios/managing-local-principals/principals-manager#groups)
  or [Grouping people together](~peios/managing-local-principals/creating-accounts#grouping-people-together).
- **Inspect or change privileges and integrity policy:** [Assigning privileges](~peios/managing-local-principals/assigning-privileges).
  This is the machine's local policy, separate from the account's identity.
  A policy change affects newly minted sign-in tokens, not existing tokens.
- **Change your own password or SSH keys:** [Sign in](~peios/signing-in/overview#manage-your-own-credentials)
  links the self-service procedures.

## Keep a usable administrator route

Before changing an administrator's credentials, membership or sign-in access,
keep a working administrator session and verify the replacement route. The
[last-administrator guard](~peios/managing-local-principals/creating-accounts#the-last-administrator-guard)
checks account state; it does not prove that you can actually sign in through a
usable route. SSH configuration changes can end every SSH session, so follow
the [separate-access precautions](~peios/signing-in/signing-in-over-ssh) there.

Read [Disabling rather than deleting](~peios/managing-local-principals/creating-accounts#disabling-rather-than-deleting)
before removing an account. Recreating a name does not restore the old SID or
the access granted to it.

## Understand the model when needed

Security Fundamentals explains [authorities and principal sources](~peios/authentication/principal-sources),
[local identity storage](~peios/authentication/the-local-store),
[name resolution](~peios/authentication/resolving-names) and
[privileges](~peios/privileges/overview). Tool authors and administrators
investigating a refused request can consult the
[local principal interfaces](~peios/local-principal-interfaces/the-admin-socket)
in the technical reference.

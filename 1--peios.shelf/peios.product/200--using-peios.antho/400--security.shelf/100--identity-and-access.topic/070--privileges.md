---
title: Privileges
type: concept
description: What a privilege allows, how machine policy rather than group membership assigns privileges, the states a privilege has on a token, and the privileges you meet most often.
related:
  - peios/identity-and-access/access-tokens
  - peios/authentication/granting-access
  - peios/identity-and-access/integrity-levels
---

A privilege lets a program perform a system operation that has no object to
put a permission on: shutting down the machine, setting the clock, or loading
a kernel module. Permissions live on objects, and privileges live on the
program asking. Some privileges also let a program reach objects in ways their
permissions alone wouldn't allow, such as reading a file for a backup.

## Policy assigns privileges

Privileges come from machine policy, not from who you are. Belonging to the
Administrators group gives an account no privilege by itself. When you sign
in, authd reads the policy under `Machine\Generic\Authn\Policy`, combines the
privileges granted to your account and to each of your groups, and puts the
result in your [access token](~peios/identity-and-access/access-tokens).

The policy that Peios ships gives every account a small set of privileges
and gives Administrators many more, such as `SeShutdownPrivilege` and
`SeBackupPrivilege`. It deliberately gives no one the privileges that create
or install tokens. [Granting Access](~peios/authentication/granting-access)
explains the policy and how to change it.

A token keeps the privileges it was created with. A change to policy reaches
only tokens created after it, so sign in again to pick it up.

## Privilege states

A privilege on a token is in one of these states:

- **Present.** The token has the privilege. A privilege can't be added to a
  token after it is created.
- **Enabled.** The privilege is in effect. A program can use a privilege only
  while it is both present and enabled. authd creates tokens with every
  granted privilege enabled.
- **Removed.** The privilege is gone from the token for good. Removing a
  privilege can't be undone, unlike turning it off.

A program that needs a privilege only for a moment can turn it off when it is
done, or remove it, so a later mistake can't use it.

## Common privileges

These are the privileges you are most likely to see in a token or a policy:

| Privilege | Allows |
|---|---|
| `SeChangeNotifyPrivilege` | Passing through directories without permission to each one. Every account has it. |
| `SeShutdownPrivilege` | Shutting down or rebooting the machine |
| `SeRemoteShutdownPrivilege` | Shutting down or rebooting from a remote session, in addition to `SeShutdownPrivilege` |
| `SeBackupPrivilege` | Reading any object for a backup, whatever its permissions |
| `SeRestorePrivilege` | Writing any object to restore a backup, whatever its permissions |
| `SeTakeOwnershipPrivilege` | Taking ownership of any object |
| `SeSecurityPrivilege` | Reading and changing an object's audit settings |
| `SeSystemtimePrivilege` | Changing the system clock |
| `SeImpersonatePrivilege` | Acting for a client with the client's identity |
| `SeManageVolumePrivilege` | Mounting and managing volumes |
| `SeLoadDriverPrivilege` | Loading and unloading kernel modules |
| `SeDebugPrivilege` | Inspecting and attaching to any process, whatever its permissions |
| `SeTcbPrivilege` | Operations reserved for the system's most trusted components |

Privilege names are case-sensitive: write them exactly as shown.

A privilege doesn't override every protection. `SeBackupPrivilege` and
`SeRestorePrivilege` apply only when a program asks for backup or restore
access explicitly. Neither they nor `SeDebugPrivilege` bypass Process
Integrity Protection, which guards trusted processes and the objects labeled
for them.

The kernel's [privilege catalog](~kernel/internals/kacs/privileges/privilege-catalogue)
is the complete list, with each privilege's exact effect.

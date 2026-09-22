---
title: The passwd command
type: reference
description: passwd changes your own password — the authority proves your current password and sets the new one with whichever principal source holds your account.
related:
  - peios/signing-in/overview
  - peios/signing-in/the-login-command
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/creating-accounts
  - peios/privileges/assigning-privileges
---

`passwd` changes your own password.

```
passwd
```

It takes no arguments. The account it changes is the one you are signed in as: the authority reads it from your token, and the request has no field in which to name anybody else. To set another principal's password, an administrator uses [`lps password`](~peios/managing-local-principals/lps-command).

## What it asks

```
$ passwd
Changing the password for alice
Current password:
New password:
Retype new password:
password changed
```

Your current password is always asked for, even though you are signed in. Being signed in shows that someone authenticated as you; it does not show that the person at the keyboard now is you, and a password changed from an unattended terminal could not be recovered by signing in again.

If the new password and its confirmation differ, or the new one is empty, you are told why and asked again. After three attempts the change ends with the password unchanged.

The prompts come from the principal source that holds your account, not from `passwd`. `passwd` renders what it is asked and returns the answers, so a source with different requirements asks for what it needs without `passwd` changing.

## How it works

`passwd` opens a credential-change conversation with the authority on `/run/logon.sock` ([PGSS §2.20](~peios/logon/credential-change)). `authd` finds the source that holds your account from your token's SID and relays the conversation to it. `lpsd` checks your current password, sets the new one, and writes its store to disk before it reports success, so `password changed` means the next sign-in checks the new password.

Nothing is minted. Your current session carries on as it was, and so does every other session you hold.

## From a script

When standard input is not a terminal, `passwd` prints no prompts and reads one line for each, in order:

```
printf '%s\n' "$current" "$new" "$new" | passwd
```

## When it refuses

| Message | Meaning |
|---|---|
| `Authentication failed.` | The current password was wrong, or the password was reset by an administrator while you were changing it. |
| `This account has no password to change. …` | The account signs in with no password, or exists only to run a service. An administrator can give it one with `lps password`. |
| `This account is disabled.` | An administrator has disabled the account. |
| `This account has no credential that can be changed here.` | You are signed in as an identity that no principal source holds, such as `SYSTEM`. |
| `Too many attempts. The password is unchanged.` | The new password was refused three times. |
| `cannot reach the authority …` | `authd` is not running. |
| `permission denied connecting to /run/logon.sock …` | This machine's logon socket does not admit you. See below. |

A message ending `whether the password changed is not known` means the authority went away after the change was asked for and before it said how it ended. Sign in with each password to find out which one holds.

## Who can reach the socket

Every authenticated principal can connect to `/run/logon.sock` so that `passwd` works for them. That does not let them originate a logon for anybody else, which still takes a `LogonTypes` record on their own policy entry.

A machine whose administrator has replaced the socket's descriptor with `LogonSocketDescriptor` may not admit you. See [assigning privileges](~peios/privileges/assigning-privileges).

## Exit status

| Code | Meaning |
|---|---|
| 0 | The password was changed. |
| 1 | The change was refused or failed, or the authority could not be reached. |
| 2 | The command line was wrong. |

## See also

- [Signing in](~peios/signing-in/overview) — the conversation this is one kind of.
- [The `lps` command](~peios/managing-local-principals/lps-command) — setting another principal's password, as an administrator.
- [PGSS §2.20](~peios/logon/credential-change) — the credential-change conversation, specified.

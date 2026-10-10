---
title: The passwd command
type: reference
description: passwd changes your own password — the authority proves your current password and sets the new one with whichever principal source holds your account.
related:
  - peios/signing-in/overview
  - peios/signing-in/the-login-command
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/creating-accounts
  - peios/managing-local-principals/assigning-privileges
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

`passwd` opens a credential-change conversation with the authority on `/run/logon.sock` ([PGSS §2.20](~peios/logon/credential-change)). `authd` finds the source that holds your account from your token's SID and relays the conversation to it. `lpsd` checks your current password, sets the new one, and writes its store to disk before it reports success, so `password changed` means the next sign-in checks the new password. It records the change as an `lpsd.credential.changed` event, naming your account by SID, and records a refused change the same way with the reason, such as `wrong-credential` for a current password that did not verify.

Nothing is minted. Your current session carries on as it was, and so does every other session you hold.

## Other ways to change it

`passwd` is one client of this conversation, not the only one. A program can hold the same conversation for you. On the desktop, **My Settings** (type `my` in the launcher) does: its **Password** section collects your current password and the new one twice, and hands them over when the authority asks. The line along the bottom of the window shows what the authority said, then whether the password changed, and the fields are emptied whatever happened. An account with no password sees why in place of the form. The authority asks the same questions, applies the same rules and gives the same refusals whichever program asks; only how the questions are shown differs. A program written in Rust gets the conversation from the `credential` module of `libauthd-client`, which `passwd` itself uses.

Adding or removing your own SSH keys is a sibling conversation on the same socket, and asks for your current password the same way: see [Changing your own keys](~peios/managing-local-principals/lps-command#changing-your-own-keys).

## From a script

When standard input is not a terminal, `passwd` prints no prompts and reads one line for each, in order:

```
printf '%s\n' "$current" "$new" "$new" | passwd
```

## When it refuses

| Message | Meaning |
|---|---|
| `Authentication failed.` | The current password was wrong, or the password was reset by an administrator while you were changing it. |
| `This account has no password to change. …` | The account has no password available for this change, or exists only to run a service. For an ordinary account, an administrator can set a password with `lps password` and select a policy that allows it with `lps policy`. A service principal cannot be given a credential. |
| `This account is disabled.` | An administrator has disabled the account. |
| `This account has no credential that can be changed here.` | You are signed in as an identity that no principal source holds, such as `SYSTEM`. |
| `Too many attempts. The password is unchanged.` | The new password was refused three times. |
| `cannot reach the authority …` | `authd` is not running. |
| `permission denied connecting to /run/logon.sock …` | This machine's logon socket does not admit you. See below. |

A message ending `whether the password changed is not known` means the authority went away after the change was asked for and before it said how it ended. Sign in with each password to find out which one holds.

## Who can reach the socket

Every authenticated principal can connect to `/run/logon.sock` so that `passwd` works for them. That does not let them originate a logon for anybody else, which still takes a `LogonTypes` record on their own policy entry.

A machine whose administrator has replaced the socket's descriptor with `LogonSocketDescriptor` may not admit you. See [assigning privileges](~peios/managing-local-principals/assigning-privileges).

## Exit status

| Code | Meaning |
|---|---|
| 0 | The password was changed. |
| 1 | The change was refused or failed, or the authority could not be reached. |
| 2 | The command line was wrong. |

## See also

- [How authentication works](~peios/authentication/overview) — the conversation this is one kind of.
- [The `lps` command](~peios/managing-local-principals/lps-command) — setting another principal's password, as an administrator.
- [PGSS §2.20](~peios/logon/credential-change) — the credential-change conversation, specified.

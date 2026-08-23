---
title: Creating accounts
type: how-to
description: How the first account on a machine comes to exist, how to create the ones after it, and what happens on an image that ships a development account.
related:
  - peios/managing-local-principals/overview
  - peios/managing-local-principals/the-local-store
  - peios/managing-local-principals/lps-command
  - peios/boot-and-trust-establishment/overview
---

## Creating an account

Run `lps add` with no arguments and it asks for what it needs:

```
$ lps add
Name: alice
Full name [optional]: Alice Chen
Additional groups [comma-separated, optional]: Administrators
Primary group [the daemon's default]:
Home directory [the daemon's default]:
Shell [the daemon's default]:
Password for alice:
Again:

  name           alice
  full name      Alice Chen
  primary group  (the daemon's default)
  home           (the daemon's default)
  shell          (the daemon's default)
  groups         Administrators

Create this principal? [Y/n]:
created alice with RID 1002
```

An empty answer takes the default, and nothing is sent until you confirm. Or say it all on one line:

```
$ lps add alice --group Administrators
```

Anything you supply is not asked for, so either style works and they mix freely.

Groups are named however you like — `Administrators`, a local group's name, or a literal SID such as `S-1-5-32-544`. `lpsd` resolves it.

You need to be an administrator to do this. See [the `lps` command](~peios/managing-local-principals/lps-command) for the full surface.

### What a new account gets

| | |
|---|---|
| RID | The next one. Never chosen, never reused. |
| uid | The RID, plus this machine's base — so RID 1000 signs in as 1001000. |
| Primary group | `Authenticated Users`, unless you say otherwise. |
| Home | `/home/<name>` |
| Shell | `/bin/sh` |

**No per-user group is created.** That Linux convention exists so a file's *group* ownership means something, and under KACS it means nothing — access is decided by the token, not by the mode bits. A group per user would be ceremony with a RID attached.

**The home directory is not created either.** `lps` records the path; nothing makes the directory. A principal whose home is missing still signs in, starting in `/`, and `login` says so.

## Accounts with no password

`lps add <name> --no-password` creates a principal who signs in without being asked for anything.

The sign-in is otherwise completely ordinary. `lpsd` still vouches for the principal, `authd` still mints the token and still applies this machine's privilege and integrity policy to it, and the session that results is indistinguishable from one reached by typing a password. Nothing is bypassed; there is simply nothing to collect.

**It is a property of the account.** Nothing ties it to a particular terminal, so the principal can be signed in at any logon prompt the machine offers — the console today, a remote one later. If what you want is "this console signs in automatically", a passwordless account is how Peios spells it, and the breadth is the cost.

An empty password is not the same thing and is refused. See [the `lps` command](~peios/managing-local-principals/lps-command).

## Give the first account Administrators

On a stock machine the tree-wide security descriptor grants `LocalSystem` and `BUILTIN\Administrators`, and nothing else.

An account without `Administrators` can traverse to a file it names exactly, and can execute it — but it cannot *list a directory*, because nothing bypasses that check. The symptom is a shell that appears to work until you type `ls`.

That is a limit of the descriptor the system ships with rather than anything about the account. Until per-subtree descriptors exist, an ordinary non-administrative account on a stock image is not comfortable to use.

## Where the first account comes from

A machine with no store provisions one at first boot, and it is **empty** — `lpsd` generates the domain, because a source with no domain can answer nothing, but it does not invent accounts.

So something has to create the first one, and there is a chicken-and-egg problem: `lps` talks to `lpsd`, so `lpsd` must already be running, which means this cannot be done by an early-boot script. Autorun scripts run before any service has started.

The answer is a **oneshot service**, ordered after `lpsd`, that runs `lps` like anything else would. On a development image that service exists and creates a known account. On a production image it does not, and an administrator creates the first account themselves.

### On a development image

Images built for development ship two things: a script that creates a known account, and a registry seed defining the oneshot service that runs it. If your image has them, it boots with an account already present, and `lps list` will show it.

**On a live image that account has no credential at all**, and it is an administrator. The script creates it with `lps add peios --group Administrators --no-password`, so anyone who reaches a logon prompt on that machine can become it — and the console signs in as it automatically, without asking anything.

That is deliberate rather than an oversight. A live ISO is an unauthenticated medium: anyone holding it can boot it and read everything on it, so a password would be a formality rather than a boundary, and one printed in the image at that. What it is *not* is a posture to carry anywhere else.

Give it a password the moment the machine becomes something you care about, which turns it into an ordinary account and stops the console signing in on its own:

```
$ lps password peios
New password for peios:
Again:
set the password for peios
```

Better still, build an image without the seed. See *On an image without one* below.

### On an image without one

`lpsd` starts, provisions an empty store, and logs that no principals exist and no logon can succeed until one is created. The login prompt will appear and nothing will satisfy it.

That is the correct behaviour rather than a fault, but it does mean you need a way in. Create the first account from a console session that is already `SYSTEM` — `lps` accepts `LocalSystem` as well as administrators, precisely for this case.

## Disabling rather than deleting

```
$ lps disable guest
disabled guest
```

A disabled account keeps its RID, its SID, and its group memberships. It simply cannot sign in. Re-enable it with `lps enable`.

Prefer this to `lps remove`. A removed principal's SID keeps appearing in the security descriptors of everything they owned, and because RIDs are never reused nothing will ever hold that SID again — the files become owned by a principal that no longer resolves.

## You cannot lock yourself out

`lps` refuses to remove the last enabled administrator, to disable them, or to take `Administrators` away from them.

```
$ lps disable jack
lps: jack is the only principal who can administer this machine; disabling them would leave no way back in
```

The check counts only *enabled* administrators, so a disabled standby account does not license removing the working one.

This guard exists because there is currently no offline repair. `lps` reaches the store only through `lpsd`, and `lpsd` only authenticates — so a machine with no enabled administrator has no way back short of editing its disk from another system.

## Grouping people together

For anything beyond the built-in groups, create one:

```
$ lps group create developers
created the group developers with RID 1001
$ lps group add alice developers
added alice to developers
```

A local group is a real object with its own SID and gid, so it can be named in a security descriptor and it shows up in `getgroups`. Deleting one is refused while anybody is still in it.

## Changing your own password

Not yet. `lps password` is an administrator resetting somebody else's.

Changing your *own* password will go over PGSS Logon rather than through `lps`, so that it works the same way whichever source holds your account — a domain principal will change their password exactly as a local one does. Until then, an administrator resets it for you.

## Where to go next

For the full command surface — every flag, the group and claim subcommands, and the exit statuses — read [The `lps` command](~peios/managing-local-principals/lps-command).

For what the store holds and why RIDs are never reused, read [The local store](~peios/managing-local-principals/the-local-store).

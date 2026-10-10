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

**The home directory is not created here.** `lps` records the path and nothing more. The directory appears at the principal's **first sign-in**, made by the authority when it grants the logon — and only when the account has a home recorded, which is why a service principal never grows one.

The shipped authd service explicitly retains `SeRestorePrivilege` so it can
assign the new directory's owner and group to that principal. Removing it
from `RequiredPrivileges` can leave a newly created home accessible only to
SYSTEM and Administrators, preventing an ordinary user's session from
starting there. Authd reports this failure and leaves existing directories
alone; an administrator must repair their descriptors deliberately.

It is created owned by the principal, with a protected DACL: full control for its owner, for SYSTEM and for Administrators, and nothing for anybody else. Protected matters — without it the root's inheritable "Everyone may read" ACE would apply and every account could read every other account's files.

A principal whose home could not be created still signs in, starting in `/`, and `login` says so. A directory is not worth failing a logon over.

An existing directory is left exactly as it is, and one owned by somebody else is reported rather than taken over. So pointing a new account's home at another principal's directory does not hand it over — it produces a warning in the log and an account that starts somewhere it does not own.

## Accounts with no password

`lps add <name> --no-password` creates a principal whose credential policy is `none`. It signs in without being asked for anything where the client and authority permit credential-free sign-in.

The sign-in is otherwise completely ordinary. `lpsd` still vouches for the principal, `authd` still mints the token and still applies this machine's privilege and integrity policy to it, and the session that results is indistinguishable from one reached by typing a password. Nothing is bypassed; there is simply nothing to collect.

**It is a property of the account.** Nothing ties it to a particular terminal: any client that permits credential-free sign-in can use it, subject to the account's logon-type restrictions and the authority's policy for that client. [SSH](~peios/signing-in/signing-in-over-ssh) does not permit it; SSH requires an actual password or an enrolled key and a policy that allows that credential. A passwordless account enables console autologon, but do not assume that its use is limited to that console.

An empty password is not the same thing and is refused. See [the `lps` command](~peios/managing-local-principals/lps-command).

## Make the first account an administrator

An ordinary account is usable on a stock image. The descriptor the system tree ships with grants `Everyone` read and execute — and on Peios execute is also traverse — so any principal can list directories, read the system tree and run what is in it. What it cannot do is *write* there. A non-administrator writes only where something grants it: its own home directory, which is created at first sign-in with a protected DACL admitting the owner, `LocalSystem` and `BUILTIN\Administrators` and nobody else, and `/tmp`, where anyone may create files and only their owner may remove them. See [Installing to disk](~peios/disks-and-filesystems/installing-to-disk) for the root descriptor itself.

What an ordinary account cannot do is administer the machine. `lps` refuses it, so it cannot create the next account; it cannot mount a filesystem, install a package or change a service definition either. The first account is therefore an administrator because nothing else on the machine can make one, and it stays one because `lps` will not leave the machine without an enabled administrator (see *The last-administrator guard* below). The accounts after it need `Administrators` only if they are going to administer.

## Where the first account comes from

A machine with no store provisions one at first boot, and it is **empty** — `lpsd` generates the domain, because a source with no domain can answer nothing, but it does not invent accounts.

So something has to create the first one, and there is a chicken-and-egg problem: `lps` talks to `lpsd`, so `lpsd` must already be running, which means this cannot be done by an early-boot script. Autorun scripts run before any service has started.

The answer is a **oneshot service**, ordered after `lpsd`, that runs `lps` like anything else would. On a development image that service exists and creates a known account. On a production image it does not, and an administrator creates the first account themselves.

### On a development image

Images built for development ship two things: a script that creates a known account, and a registry seed defining the oneshot service that runs it. If your image has them, it boots with an account already present, and `lps list` will show it.

**On a live image that account has no credential at all**, and it is an administrator. The script creates it with `lps add peios --group Administrators --no-password`, so anyone who reaches a prompt that permits credential-free sign-in on that machine can become it — and the console signs in as it automatically, without asking anything.

That is deliberate rather than an oversight. A live ISO is an unauthenticated medium: anyone holding it can boot it and read everything on it, so a password would be a formality rather than a boundary, and one printed in the image at that. What it is *not* is a posture to carry anywhere else.

Give it a password the moment the machine becomes something you care about, then say it signs in with that password. The two together turn it into an ordinary account and stop the console signing in on its own:

```
$ lps password peios
New password for peios:
Again:
set the password for peios
$ lps policy peios password
credential policy updated
```

The password alone changes nothing: until `lps policy` says otherwise, the account still signs in with nothing. Set the password first, since a policy of `password` is refused for the last administrator while they have none.

Better still, build an image without the seed. See *On an image without one* below.

### On an image without one

`lpsd` starts, provisions an empty store, and logs that no principals exist and no logon can succeed until one is created. The login prompt will appear and nothing will satisfy it.

That is the correct behaviour rather than a fault, but it does mean you need a way in. Create the first account from a console session that is already `SYSTEM` — `lps` accepts `LocalSystem` as well as administrators, precisely for this case.

## Disabling rather than deleting

```
$ lps disable guest
disabled guest
```

A disabled account keeps its RID, its SID, and its group memberships. It cannot start a new sign-in. Re-enable it with `lps enable`.

Disabling an account, changing its password or removing a key does not revoke already issued tokens or end its existing sessions. Use [Task Manager's sign-out action](~peios/threads-and-processes/task-manager#signing-someone-out) when existing sessions must end. Signing out ends processes and can lose unsaved work; [session lifecycle](~peios/logon-sessions/lifecycle) explains its permissions and limits, including token references held outside those processes.

Prefer this to `lps remove`. A removed principal's SID keeps appearing in the security descriptors of everything they owned, and because RIDs are never reused nothing will ever hold that SID again — the files become owned by a principal that no longer resolves.

<span id="you-cannot-lock-yourself-out"></span>
<span id="creating-accounts--you-cannot-lock-yourself-out"></span>
<span id="managing-local-principals-creating-accounts--you-cannot-lock-yourself-out"></span>
<span id="security-fundamentals-managing-local-principals-creating-accounts--you-cannot-lock-yourself-out"></span>

## The last-administrator guard

This is a guard on the local account store, not a guarantee that a usable sign-in path is reachable.

`lps` refuses to remove the last enabled administrator, to disable them, or to take `Administrators` away from them. It refuses as firmly to leave them no way to sign in: no kind of sign-in at the machine, remotely or over the network (`lps logon-types`), or nothing to sign in with (`lps policy` and `lps key remove`).

```
$ lps disable jack
lps: jack is the only principal who can administer this machine; disabling them would leave no way back in
```

The check counts only *enabled* administrators, so a disabled standby account does not license removing the working one.

The guard does not check that a console, remote service or network route is available. After changing credentials or sign-in policy, inspect the account with `lps show <name>` and verify a fresh sign-in through the intended path before closing your working administrator session. A stored credential and a permitted logon type are not evidence that the whole path works.

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

Run [`passwd`](~peios/signing-in/the-passwd-command). It asks for your current password and then the new one:

```
$ passwd
Changing the password for alice
Current password:
New password:
Retype new password:
password changed
```

It goes over PGSS Logon rather than through `lps`, so it works the same way whichever source holds your account — a domain principal changes their password exactly as a local one does. `lps password` is the other operation: an administrator setting somebody else's.

An account created with `--no-password` has no current password to prove, so it cannot give itself one. An administrator sets one with `lps password`, and `lps policy <name> password` to have it used, or with Principals Manager's **Set password**, which does both.

## Where to go next

For the full command surface — every flag, the group and claim subcommands, and the exit statuses — read [The `lps` command](~peios/managing-local-principals/lps-command).

For what the store holds and why RIDs are never reused, read [The local store](~peios/managing-local-principals/the-local-store).

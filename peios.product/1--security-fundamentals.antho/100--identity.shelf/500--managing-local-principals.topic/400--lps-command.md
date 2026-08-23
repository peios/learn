---
title: The lps command
type: reference
description: The lps command administers the local principal store — principals, passwords, groups and memberships, profiles, and claims.
related:
  - peios/managing-local-principals/overview
  - peios/managing-local-principals/creating-accounts
  - peios/managing-local-principals/the-admin-socket
  - peios/logon-sessions/logonse-command
---

`lps` administers the **local principal store** — this machine's own accounts and groups, held by `lpsd`.

```
lps subcommand [arguments]
```

It is a client and nothing more. It holds no state, opens no store, and has no privilege of its own: every command is a request over `/run/lpsd/admin.sock` that `lpsd` decides whether to honour. `lpsd` must be running.

You must be a member of `BUILTIN\Administrators` — enabled, not deny-only — or be `LocalSystem`.

## Naming a group

Anywhere `lps` takes a group, you may write it three ways:

```
lps group add jack Administrators              # a well-known name
lps group add jack BUILTIN\\Administrators      # the same, qualified
lps group add jack developers                  # a local group
lps group add jack S-1-5-32-544                # a literal SID
```

Names are matched case-insensitively, and **`lpsd` resolves them, not `lps`**. The tool carries no copy of the well-known table and does not know this machine's domain — a second copy of the machine's identity scheme would be free to disagree with the first.

A well-known name always wins over a local group of the same name, which is why you cannot create a local group called `Administrators`.

## Inspecting

### `lps list`

Every principal, with RID, uid, state, and how many groups each is in.

```
$ lps list
NAME     RID       UID  STATE     GROUPS
jack    1000   1001000  enabled   1
guest   1001   1001001  disabled  0
```

A `-` in the UID column means nothing numbers that principal — `authd` has assigned this machine no identifier range, and they will sign in as `nobody`. See [the local store](~peios/managing-local-principals/the-local-store).

### `lps show <name>`

One principal in full.

```
$ lps show jack
name           jack
display name   Jack Palfrey
rid            1000
sid            S-1-5-21-2847362817-1094533892-3310298447-1000
uid            1001000
state          enabled
primary group  Authenticated Users [S-1-5-11]
home           /home/jack
shell          /bin/sh
groups         Administrators [S-1-5-32-544]
               developers [S-1-5-21-2847362817-1094533892-3310298447-1001] (gid 1001001)
claims         Department (string) = "Engineering"
```

Groups show a name where this machine knows one, and always show the SID. The two are kept side by side deliberately: the name is what you recognise, the SID is what a security descriptor actually holds, and the moment they disagree is exactly when you need to see both.

Only *local* groups show a gid. `lpsd` numbers the groups it owns and nothing else — `Administrators` and `Authenticated Users` are numbered by `authd`, from a table below every source's range, so `lpsd` genuinely does not know their gid and does not guess. To see the numbers a running session actually holds, read `Groups:` in `/proc/self/status`.

### `lps domain`

This machine's domain SID — the namespace every local principal and local group is numbered under.

```
$ lps domain
S-1-5-21-2847362817-1094533892-3310298447
```

Generated at first boot and unique to this machine.

## Creating and removing principals

### `lps add [name] [options]`

Creates a principal. Run with no arguments, it asks for what it needs:

```
$ lps add
Name: alice
Full name [optional]: Alice Chen
Additional groups [comma-separated, optional]: Administrators, developers
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
  groups         Administrators, developers

Create this principal? [Y/n]:
created alice with RID 1002
```

Any option you supply is not asked for, so scripted invocations keep working unchanged:

| Option | Effect |
|---|---|
| `--group <group>` | A membership. Repeatable. |
| `--primary-group <group>` | The group that becomes the POSIX gid. |
| `--home <path>` | Home directory. Must be absolute. |
| `--shell <path>` | Login shell. Must be absolute. |
| `--display-name <text>` | A human's name for a human to read. |
| `--disabled` | Create it unable to sign in. |
| `--no-password` | Create a principal that authenticates with no credential at all. See below. |
| `--no-prompt` | Fail rather than ask for anything missing. |

Nothing is sent until you confirm, so answering `n` creates nothing.

**`lps` never prompts when standard input is not a terminal.** A prompt down a pipe would consume the next line of whatever is driving the tool. See *From a script* below.

The RID is allocated by `lpsd` and reported back. You do not choose it, and the uid follows from it.

#### `--no-password`

Creates a principal who signs in without being asked for anything. No password is collected, including in the interactive flow — an operator who has said the account needs no credential is not then asked to invent one.

```
$ lps add kiosk --group Administrators --no-password --no-prompt
created kiosk with RID 1003
```

**This is a property of the account, not of a terminal.** Nothing scopes it to the console: the principal can be signed in at any logon prompt the machine offers, now or later. That is the right posture for a live image, where the medium is unauthenticated anyway and anyone holding it can read everything on it. It is the wrong posture for almost anything else.

An empty password is **not** a way to spell this, and `lps` refuses one:

```
$ lps add alice
...
Password for alice:
Again:
lps: an empty password is not a password: pass --no-password to create a
principal that authenticates without one
```

The two produce accounts that behave differently — an empty password is still collected, still prompted for, and still has to be answered — so having both spellings would mean two things that look identical at creation and diverge at every sign-in. `lpsd` refuses an empty password too, so the rule holds however the request arrives.

### `lps remove <name>`

Deletes a principal.

The RID is **not** reclaimed. Files the principal owned keep naming a SID that now resolves to nobody, and nothing will ever hold that SID again. `lps disable` is usually what you wanted — see [creating accounts](~peios/managing-local-principals/creating-accounts).

## Enabling and disabling

### `lps enable <name>` / `lps disable <name>`

A disabled principal keeps everything except the ability to sign in.

Both are refused if they would leave the machine with no enabled administrator.

## Passwords

### `lps password <name>`

Sets a principal's password, prompting twice.

```
$ lps password jack
New password for jack:
Again:
set the password for jack
```

This is an administrator resetting somebody else's password. Changing your own will go over PGSS Logon instead, so that it works identically whichever source holds your account.

An empty password is refused here for the same reason it is refused at creation. Giving a passwordless principal a password works and makes them an ordinary account; there is currently no command that takes one away again, so a principal created with `--no-password` can gain a credential but not shed one.

**From a script**, `lps` reads a single line from standard input when it is not attached to a terminal, and does not ask for confirmation:

```
printf '%s\n' "$password" | lps add alice --group Administrators --no-prompt
```

## Profiles

### `lps set <name> [options]`

Changes part of a profile, leaving the rest alone.

```
$ lps set jack --shell /bin/bash --display-name "Jack Palfrey"
updated jack
```

| Option | Effect |
|---|---|
| `--home <path>` | Home directory. Absolute. |
| `--shell <path>` | Login shell. Absolute. |
| `--display-name <text>` | Empty clears it. |
| `--primary-group <group>` | Which group projects to the POSIX gid. |

None of this is identity — no security descriptor names a home directory, and the token carries none of it. It is what `login` needs in order to start a session, and it reaches `login` on the logon reply itself.

**`lps` does not create the home directory.** It records the path. A principal whose home does not exist still signs in, starting in `/`, and `login` says so.

The primary group need not be a membership: `authd` adds it to the token if it is missing, so the order of two commands does not matter.

## Groups

Local groups are objects with a name, a RID and a gid — unlike well-known groups, which exist on every Peios machine and are not stored here.

### `lps group list`

```
$ lps group list
NAME          RID       GID  MEMBERS  SID
developers   1001   1001001        2  S-1-5-21-2847362817-1094533892-3310298447-1001
```

`MEMBERS` counts principals in *this* store, which is the only count `lpsd` can answer for.

### `lps group create <name>` / `lps group delete <name>`

```
$ lps group create developers
created the group developers with RID 1001
```

Deleting is refused while anyone is still a member, or while the group is anybody's primary group. Either would leave a record pointing at something that no longer exists.

### `lps group add <name> <group>` / `lps group remove <name> <group>`

```
$ lps group add alice Administrators
added alice to Administrators
```

Removing `BUILTIN\Administrators` is refused if it would leave no enabled administrator.

## Claims

Claims are named, typed attributes carried on the token and read by conditional ACEs. They are how a security descriptor can say *anyone in Engineering* rather than naming principals one by one.

### `lps claim set <name> <claim> <type> [value]...`

```
$ lps claim set jack Department string Engineering
set the claim Department on jack
$ lps claim set jack Level int64 7
set the claim Level on jack
```

| Type | Values |
|---|---|
| `int64` | Signed integers |
| `uint64` | Unsigned integers |
| `boolean` | `true`/`yes`/`1` or `false`/`no`/`0` |
| `string` | Text |
| `sid` | SIDs, in `S-1-…` form |
| `octet` | Hexadecimal, even length |

A claim may hold several values, and may hold none — `lps claim set jack Department string` empties it, which is different from removing it.

Claim names are matched case-insensitively, so setting `department` replaces `Department`.

### `lps claim remove <name> <claim>`

```
$ lps claim remove jack Department
removed the claim Department from jack
```

**A claim reaches a principal at their next sign-in.** A token's claims are fixed when it is minted, so setting one changes nothing for a session already running.

## Exit status

| Code | Meaning |
|---|---|
| 0 | Succeeded |
| 1 | `lpsd` refused the request, or could not be reached |
| 2 | The command line was wrong |

The split lets a script distinguish "I called this incorrectly" from "it was refused".

## Common failures

**`cannot reach lpsd … it does not appear to be running`** — `lpsd` is not up. It exits if it cannot reach `authd`, or if the store will not read; check its logs before restarting it.

**`permission denied`** — you are not an administrator, or the socket's descriptor does not admit you. See [the administrative socket](~peios/managing-local-principals/the-admin-socket).

**`there is no principal named …`** — names are case-insensitive, so this means the account genuinely is not there. `lps list` will show what is.

**`there is no group named … and it is not a SID`** — the name matched no well-known group and no local one, and does not parse as a SID. `lps group list` shows the local ones.

---
title: Principals Manager
type: how-to
description: See this machine's users and groups from the desktop — who each is, what groups they are in, who is in each group, how they may sign in, what claims they carry and what privileges they get — and, as an administrator, make, change, rename, disable and delete users and groups, set what users sign in with, their SSH keys and their claims, and change the privileges this machine gives.
related:
  - peios/managing-local-principals/overview
  - peios/managing-local-principals/lps-command
  - peios/managing-local-principals/resolving-names
  - peios/managing-local-principals/the-admin-socket
---

**Principals Manager** shows this machine's **principals**, the users and
groups it knows, and lets an administrator manage the local ones. A
*local* principal is one this machine holds itself, in `lpsd`'s store; a
*built-in* one, such as `SYSTEM` or `Administrators`, is the same on
every Peios machine and is defined by `authd`.

Start it from the launcher: **Principals Manager**.

## Users and groups

**Users** and **Groups**, in the bar, switch between the two lists.

- A user is listed with their full name, if they have one, whether they
  are local or built-in, and whether they are enabled. A disabled user
  keeps everything but can't sign in, and is greyed.
- A group is listed with whether it is local or built-in, how many
  members it has, and its description: what it is for. Some built-in
  groups, such as `Everyone`, have no list of members at all: who is in
  them is decided by a rule as each person signs in, and they say **By
  rule**.

Type in **Find** to narrow the list to names, full names, descriptions or
SIDs containing what you type.

## A user or group in full

Select one to see it in full on the right.

For a user, that is their user ID, primary group, home folder, shell
and SID; the kinds of sign-in they may use, such as at the machine or
over the network; the groups they are in; and their **claims**, the
named values that permissions written with conditions are checked
against. **Copy SID** copies their SID.

An administrator also sees what a local user signs in with, such as a
password or an SSH key, and their **SSH keys**: the public keys they may
sign in with over SSH, each with its label, its fingerprint and the day
it was added.

For a group, it is its description, group ID and SID, and who is in it.
Who is in a built-in group such as `Administrators` is recorded on this
machine, as a local group's is, so it is listed too. Someone whose
primary group it is, is in it.

Select a group a user is in, or a member of a group, to go to it.

## Making a user

**New user**, in the bar, or **Ctrl+N**, asks for:

- a **name**, which they sign in with;
- a **full name**, if you want one shown;
- a **password**, typed twice; or tick **Signs in without a password**,
  and nothing is asked for when they sign in, at any sign-in prompt on
  the machine;
- whether they are an **Administrator**, who may change the machine and
  its users and groups;
- a **home** folder and a **shell**, if not `/home/<name>` and
  `/bin/sh`.

**Create** makes the user with all of it, or not at all: if anything is
refused, such as a name already taken, nothing is made and the window
says why.

## Changing a user

Select a local user, and their buttons are below their details:

- **Edit** changes their full name, home, shell and primary group. Their
  home folder is made at their first sign-in, and is not moved if you
  change it. Their primary group is the one their new files belong to,
  and they are in it whatever their other groups.
- **Rename** changes the name they sign in with. They keep their SID, so
  their files, permissions and groups stay theirs. Their home stays where
  it is; change it under **Edit** if it should follow.
- **Set password** gives them a new password. A user who signed in
  without one needs it from then on. Their sessions already signed in
  carry on.
- **Sign-in** chooses what they sign in with, and the ways they may sign
  in.
  - **Signs in with**: a password, an SSH key, either, nothing (no
    password is asked for, at any sign-in prompt on the machine), or
    nothing accepted (every sign-in is refused, though nothing shows them
    as disabled). Giving them a password or a key doesn't change this, so
    a key added isn't used until this allows one.
  - **May sign in**: as the machine's default allows (at the machine, on
    a remote desktop, over the network, and the rest a person uses), or
    only the ways you tick. **To run a service** lets the service manager
    start a service as them without any password, and is never part of
    the default.
- **Add to group** puts them in a local group, or in a built-in one whose
  members are recorded here, such as `Administrators` or `Users`.
  **Remove**, beside a group they are in, takes them out of it.
- **Add**, beside **SSH keys**, adds a public key: paste one line of their
  `.pub` file, such as `~/.ssh/id_ed25519.pub`. Ed25519 keys are
  accepted, and RSA keys of 3072 to 8192 bits. Without a label, the key's
  own comment is its label. **Remove**, beside a key, removes it.
- **Add**, beside **Claims**, gives them a claim: its name, its type, and
  its values, one to a line. Each value is checked against the type, and
  one that doesn't fit is named. A claim of SIDs may name a user or group
  instead of giving a SID. **Edit** changes a claim's type and values,
  and **Remove** takes it away. A claim with no values is still a claim
  they have, which conditions treat differently from one they don't.
- **Disable** stops them signing in and keeps everything else; **Enable**
  lets them again.
- **Delete** removes them, after asking. Their SID is never given to
  anyone again, so files and permissions that name it name nobody;
  **Disable instead** is offered, and is usually what you want.

Changes to how a user signs in, to their keys, to the groups they are in
and to their claims apply from their next sign-in.

## Groups

In **Groups**, **New group** (or **Ctrl+N**) makes a local group, with a
name and a description of what it is for. Anyone may read the
description.

Select a local group, and its buttons are below its details:

- **Edit** changes its description; empty, it has none.
- **Rename** changes its name. It keeps its SID, so its members, and the
  permissions that name it, stay as they are.
- **Add member** puts a local user in it. **Remove**, beside a member,
  takes them out; a member whose primary group it is has to be given
  another under **Edit** first.
- **Delete** removes it, after asking, once nobody is in it. Its SID is
  never given to anything again.

A built-in group whose members are recorded here, such as
`Administrators`, has **Add member** and **Remove** too, but can't be
renamed, described or deleted: `authd` defines it, the same on every
Peios machine.

The machine always keeps an enabled administrator who can sign in.
Disabling or deleting the last one, taking away every way they could
sign in to administer, or leaving them nothing to sign in with, such as
removing the only key of one who signs in only with a key, is refused,
and the window says why.

## Privileges

What a person may do beyond what permissions allow them, such as back up
any file or shut the machine down, is this machine's **local policy**:
one **record** per user or group in the registry, which `authd` reads at
every sign-in. Each record may give **privileges**, an **integrity**
level, an **owner** for what they make, and a **default DACL**, the
permissions an object they make gets when it has no parent to inherit
from. See [Assigning privileges](~peios/privileges/assigning-privileges)
for what each does and how records combine.

**Privileges**, in the bar, lists the records: who each is for, how many
privileges it gives, and its integrity. A service's record is named by
the service. Select one to see it in full, each privilege with what it
lets its holder do. **Denied to everyone**, the first row, is the
privileges no record can give.

A user's page says what they would get in all if they signed in now: the
privileges, integrity, owner and default DACL that their own record,
their groups' records and `Everyone`'s come to, and which records those
are. **Signed in** chooses the kind of sign-in, such as at the machine or
over the network, since a record may be for one kind of sign-in. A
group's page says what its record gives its members.

Changing them:

- **New record** (or **Ctrl+N**) makes a record, for a user or group
  here, a well-known name such as `Everyone` or `Network`, or a SID.
  **Give them their own record**, on a user's page, and **Give it a
  record**, on a group's, do the same for them.
- **Edit** changes what a record gives: tick its privileges, choose its
  integrity, and type an owner or a default DACL, in SDDL. Anything left
  empty, the record says nothing about. A default DACL that isn't SDDL
  `authd` could use is refused.
- **Delete** removes a record, after asking. What it gave is no longer
  given.
- **Edit**, on **Denied to everyone**, chooses what no record may give.

Taking `SeChangeNotifyPrivilege` from `Everyone` or `Administrators` is
asked about first: without it, nobody who has it only from there can
pass through a folder, so no shell starts for them.

A record names a user or local group by its SID, since `authd` doesn't
ask `lpsd` what a name means; the window does this for you. What `authd`
warns about in the records is shown above the list, with why: a record it
ignores, such as one named by a name it doesn't know, or two records for
the same principal, such as `Administrators` and `S-1-5-32-544`, which
both apply and should be one.

On a machine with no policy at all, `authd` gives `Everyone`
`SeChangeNotifyPrivilege` and nothing more, and the list says so. The
first record saved makes the policy, with that in it, since once there
is a policy it is all there is.

Changes apply from each person's next sign-in.

## Changes made elsewhere

The lists are read again every few seconds, so a user, group or
privileges record added, changed or removed with `lps` or `reg`, or by
another administrator, appears without your doing anything. **Refresh**, or **F5**, reads everything at
once.

## What you may see and change

Anyone may see the users and groups: the identity socket that
Principals Manager reads them from answers everyone.

What a user signs in with, and their SSH keys, are shown only to an
administrator: `lpsd` holds them, and tells nobody else. The privileges
records are shown to anyone signed in, and changed by whoever the
registry key's permissions let, which as shipped is `Administrators`.

Changing them needs `BUILTIN\Administrators`, enabled in your token, as
`lps` does. Without it, the window says **You may look, but not change
anything**, and why, and offers no changes. Built-in principals and
groups can't be renamed or deleted, and the window says so when one is
selected.

## In a terminal

`lps list` lists the users, `lps show NAME` shows one in full, and `lps
group list` lists the local groups. `getent group Administrators` lists
who is in a group, and `lps key list NAME` lists a user's keys. `lps add`,
`lps set`, `lps rename`, `lps password`, `lps policy`, `lps key`, `lps
logon-types`, `lps claim`, `lps group`, `lps disable` and `lps remove` make
the same changes as the window. See [The `lps` command](~peios/managing-local-principals/lps-command).
The privileges records are registry keys under
`Machine\Generic\Authn\Policy`, read and changed with `reg`, and `token
show --all` lists what a session's token actually holds.

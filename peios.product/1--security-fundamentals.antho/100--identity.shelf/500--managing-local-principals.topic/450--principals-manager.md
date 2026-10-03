---
title: Principals Manager
type: how-to
description: See this machine's users and groups from the desktop — who each is, what groups they are in, who is in each group, how they may sign in and what claims they carry — and why you may look but not change anything.
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
- A group is listed with whether it is local or built-in, and how many
  members it has. Some built-in groups, such as `Everyone`, have no list
  of members at all: who is in them is decided by a rule as each person
  signs in, and they say **By rule**.

Type in **Find** to narrow the list to names, full names or SIDs
containing what you type.

## A user or group in full

Select one to see it in full on the right.

For a user, that is their user ID, primary group, home folder, shell
and SID; the kinds of sign-in they may use, such as at the machine or
over the network; the groups they are in; and their **claims**, the
named values that permissions written with conditions are checked
against. **Copy SID** copies their SID.

For a group, it is its group ID and SID, and who is in it. Who is in a
built-in group such as `Administrators` is recorded on this machine, as
a local group's is, so it is listed too.

Select a group a user is in, or a member of a group, to go to it.

## Changes made elsewhere

The lists are read again every few seconds, so a user or group added,
changed or removed with `lps`, or by another administrator, appears
without your doing anything. **Refresh**, or **F5**, reads everything at
once.

## What you may see and change

Anyone may see the users and groups: the identity socket that
Principals Manager reads them from answers everyone.

Changing them needs `BUILTIN\Administrators`, enabled in your token, as
`lps` does. Without it, the window says **You may look, but not change
anything**, and why. Built-in principals and groups can't be renamed or
deleted, and the window says so when one is selected.

## In a terminal

`lps list` lists the users, `lps show NAME` shows one in full, and `lps
group list` lists the local groups. `getent group Administrators` lists
who is in a group. See [The `lps` command](~peios/managing-local-principals/lps-command).

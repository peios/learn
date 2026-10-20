---
title: Security Identifiers
type: concept
description: What a security identifier (SID) is, how to read its string form, which kinds of principal have one, and why permissions name SIDs rather than account names.
related:
  - peios/identity-and-access/well-known-sids
  - peios/identity-and-access/access-tokens
  - peios/permissions/object-policy
---

A security identifier (SID) is the value Peios uses to identify a principal: a
user, a group, a service, the machine, or a built-in identity such as
Everyone. Every permission on every object names SIDs, and every running
program carries SIDs that say who it is. When you read a permission or
diagnose a refusal, you are comparing SIDs.

## Reading a SID

A SID is binary, but tools show it as a string that starts with `S-1`:

```text
S-1-5-21-3623811015-3361044348-30300820-1013
```

The parts after `S-1` are numbers assigned by an authority. The `5` here is
the authority, and the numbers after it narrow down to one principal. The last
number is the relative identifier (RID), which tells principals apart within
the same domain. Short SIDs belong to identities that every Peios system
shares:

| SID | Identity |
|---|---|
| `S-1-5-18` | Local System, the operating system's own identity |
| `S-1-5-32-544` | The built-in Administrators group |
| `S-1-1-0` | Everyone |

These shared SIDs are called well-known SIDs. [Well-Known SIDs](~peios/identity-and-access/well-known-sids)
lists the ones you meet most often.

## Names are labels

An account's name can change. Its SID doesn't. Renaming an account keeps its
SID, so every permission that names the account still applies to it. A deleted
account's SID is never given to another account, so old permissions can't
start granting access to a stranger.

For the same reason, compare SIDs rather than names when you check who has
access. Two different strings can spell the same SID, and a name only tells
you what a tool chose to display.

A SID on its own doesn't tell you what a principal can do. Group membership,
privileges, and the other details of a principal's authority come from the
[access token](~peios/identity-and-access/access-tokens) it runs with.

## SIDs that aren't accounts

Some SIDs identify something other than a person or a group:

- **Service SIDs** identify one service, written by name as `SERVICE\loregd`.
  A service's programs carry its service SID as a group, so a permission can
  admit one service without admitting everything that runs as the same
  account.
- **Logon SIDs** identify one sign-in or other logon, in the form
  `S-1-5-5-X-Y`. They let a permission admit one session without admitting
  every session of the same account. See
  [Logon Sessions](~peios/identity-and-access/logon-sessions).
- **Integrity labels**, in the form `S-1-16-n`, mark a level of trust. See
  [Integrity Levels](~peios/identity-and-access/integrity-levels).
- **Placeholders** stand in for another identity in a permission. When a new
  object inherits a permission that names Creator Owner, for example, the new
  object's owner takes its place.

## Where SIDs are defined

The Peios Common Data Structures specification defines the
[SID format](~specifications/pcds/sid/binary-format) and the complete
[catalog of well-known SIDs](~specifications/pcds/sid/well-known-sids). It is
the authority for every assigned value.

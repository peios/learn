---
title: Well-Known SIDs
type: reference
description: The built-in security identifiers you meet most often in tokens and permissions, with their string forms and what each one matches.
related:
  - peios/identity-and-access/security-identifiers
  - peios/permissions/object-policy
---

Well-known security identifiers (SIDs) name identities that every Peios system
shares, such as Everyone or the Administrators group. They appear in tokens
and in permissions on every machine with the same value. This page lists the
ones you meet most often. The
[well-known SID catalog](~specifications/pcds/sid/well-known-sids) in the
Peios Common Data Structures specification is the complete list.

## Accounts and groups

These SIDs identify built-in accounts and groups:

| SID | Name | Identifies |
|---|---|---|
| `S-1-5-18` | Local System (SYSTEM) | The operating system itself, with the highest level of trust |
| `S-1-5-19` | Local Service | A built-in account for services that need little authority |
| `S-1-5-20` | Network Service | A built-in account for services that authenticate to other machines |
| `S-1-5-32-544` | Administrators | The built-in administrators group |
| `S-1-5-32-545` | Users | The built-in group of ordinary accounts |
| `S-1-5-32-546` | Guests | The built-in guests group |
| `S-1-5-32-551` | Backup Operators | The built-in group for backup and restore |
| `S-1-5-7` | Anonymous | A caller whose identity isn't known |

## Broad groups

These SIDs match many principals at once:

| SID | Name | Matches |
|---|---|---|
| `S-1-1-0` | Everyone | Every principal, including Anonymous |
| `S-1-5-11` | Authenticated Users | Every principal that has authenticated, which excludes Anonymous |
| `S-1-5-4` | Interactive | Principals that signed in interactively |
| `S-1-5-14` | Remote Interactive | Principals that signed in from another computer; they also carry Interactive |
| `S-1-5-2` | Network | Principals that authenticated over the network |
| `S-1-5-3` | Batch | Principals running a scheduled job |
| `S-1-5-6` | Service | Principals running as a service |

## Placeholders and patterns

These SIDs stand in for another identity or follow a pattern:

| SID | Name | Meaning |
|---|---|---|
| `S-1-3-0` | Creator Owner | In an inherited permission, replaced by the new object's owner |
| `S-1-3-4` | Owner Rights | Replaces the rights an object's owner has automatically |
| `S-1-5-5-X-Y` | Logon SID | One logon session; see [Logon Sessions](~peios/identity-and-access/logon-sessions) |
| `S-1-5-80-...` | Service SID | One service, written by name as `SERVICE\<service-name>` |
| `S-1-16-n` | Integrity label | An integrity level; see [Integrity Levels](~peios/identity-and-access/integrity-levels) |
| `S-1-0-0` | Nobody | No principal |

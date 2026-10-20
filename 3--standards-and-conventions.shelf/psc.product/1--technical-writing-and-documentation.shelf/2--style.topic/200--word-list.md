---
title: Word List
type: reference
description: How Peios documentation spells, capitalizes, and uses its own
  terms and common technical words, including logon and sign in, set up,
  back up, principal, token, and registry key, value, and layer.
---

This list records the decided form of words that Peios documentation uses
often or that are easy to get wrong. Where a term means something different
in Windows, Linux, or another project, the meaning here is the one Peios
documentation uses. Add to the list whenever a question about a word is
settled.

## Peios terms

| Term | Use | Notes |
|---|---|---|
| Peios | Peios | Not "PeiOS", "PEIOS", or "peios" in prose. |
| access control list | access control list (ACL) | "an ACL". |
| access token | access token, token | "token" alone once the context is clear. |
| principal | principal | Any entity that can be granted access: a user, a group, a service, or the machine. Not a synonym for "user". |
| registry key | key | A node in the registry tree. Not "folder". |
| registry value | value | A named, typed piece of data in a key. Not "entry" or "setting" when the value itself is meant. |
| registry layer | layer | One source of registry data that is merged with others. |
| discretionary access control list | discretionary access control list (DACL) | "a DACL". |
| logon frontend | logon frontend | A program a person signs in through, such as sshd or the console sign-in, which then asks authd for a logon. authd performs the logon; the frontend handles the sign-in. Not "login frontend". |
| logon | logon (noun and adjective) | The system creating a logon session and token for a principal: "logon session", "logon type", "logon SID", "each logon". A logon needs no sign-in; services and scheduled jobs get logons too. Not "login". There is no verb: the system "creates a logon", it does not "log the user on". |
| security descriptor | security descriptor (SD) | "an SD". |
| security identifier | security identifier (SID) | "a SID". |
| system access control list | system access control list (SACL) | "a SACL". |

## General terms

| Term | Use | Notes |
|---|---|---|
| afterwards, towards | afterward, toward | Also forward, backward, upward, and downward. No final "s". |
| back up, backup | back up (verb), backup (noun and adjective) | "Back up the key." "Restore the backup." |
| log in, login, log on | Don't use, except in literal names such as the `login` program. | Use "sign in" for providing credentials and "logon" for what the system creates. |
| set up, setup | set up (verb), setup (noun and adjective) | "Set up the network." "The setup program." |
| shut down, shutdown | shut down (verb), shutdown (noun and adjective) | |
| sign in, sign-in | sign in (verb), sign-in (noun and adjective) | Providing credentials to start a logon, by a person or a client acting for one: "Sign in to the desktop." "The sign-in screen." "An SSH client signs in with a key." A program using its own stored credentials does not sign in; it gets a logon. |
| sign out, sign-out | sign out (verb), sign-out (noun and adjective) | Not "log off" or "log out". |
| startup, start up | startup (noun and adjective), start (verb) | "At startup." "Start the service." Avoid "start up" as a verb. |
| file name | file name | Two words, except as a literal identifier. |
| home folder | home directory | Use "directory" for file system paths throughout. |
| command line | command line (noun), command-line (adjective) | |
| run, execute | run | "execute" only for the literal permission or operation. |

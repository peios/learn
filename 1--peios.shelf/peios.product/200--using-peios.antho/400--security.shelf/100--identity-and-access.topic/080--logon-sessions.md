---
title: Logon Sessions
type: concept
description: What a logon session records, how it relates to the tokens that share it, the logon types that describe how a session began, and what ending a session does.
related:
  - peios/identity-and-access/access-tokens
  - peios/local-accounts/logonse
  - peios/authentication/granting-access
---

A logon session records one occasion on which Peios established an identity:
you signing in at the console, an SSH connection, or a service starting. Every
access token belongs to exactly one logon session, and every token copied from
it shares the same session. Knowing which session a program belongs to tells
you how its identity was established, and lets you end everything that came
from one sign-in together.

A logon session is separate from a terminal's session and from a desktop
session: the word "session" names different things in each.

## What a session records

authd creates the logon session before it creates the first token for it. The
session records:

- the user's security identifier (SID);
- the logon type, which says how the session began;
- the time it was created;
- an identifier that is unique while the machine is running.

The session's logon SID, in the form `S-1-5-5-X-Y`, comes from that
identifier and is placed in the groups of every token in the session. A
permission can name the logon SID to admit one session without admitting the
account's other sessions. The identifier can recur after the machine
restarts, so don't use it as a lasting record of an account.

A session lasts as long as any token that belongs to it.

## Logon types

The logon type describes the situation, not the account: one account can
have sessions of several types at once.

| Logon type | Session begins when |
|---|---|
| `Interactive` | Someone signs in at the machine's console |
| `RemoteInteractive` | Someone signs in from another computer, over SSH or to a desktop in a browser |
| `Network` | A program on another computer authenticates to use a service here |
| `NetworkCleartext` | As `Network`, marked as using a credential that was sent unencrypted |
| `NewCredentials` | A program keeps its identity on this machine, marked as using other credentials for connections to other computers |
| `Batch` | A scheduled job starts |
| `Service` | A service starts |

Every SSH connection is `RemoteInteractive`, including a single command run
without a terminal. The names of the two variants describe their purpose, not
what happened: `NetworkCleartext` doesn't prove that credentials crossed the
network unencrypted, and `NewCredentials` doesn't make Peios forward
credentials anywhere.

Sign-in policy can permit or refuse each logon type for an account; see
[Granting Access](~peios/authentication/granting-access).

## Ending a session

Ending a logon session stops the programs whose primary token belongs to it.
authd asks them to stop, then forces them. A program elsewhere that holds a
copy of one of the session's tokens keeps the session alive, so ending it
doesn't revoke every use of its identity. The Local System and service
sessions can't be ended this way.

[Inspecting and Ending Sessions](~peios/local-accounts/logonse) describes the
`logonse` command.

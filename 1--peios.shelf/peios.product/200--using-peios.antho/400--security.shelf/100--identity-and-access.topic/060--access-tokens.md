---
title: Access Tokens
type: concept
description: What an access token holds, how a program gets one at sign-in or from its parent, the difference between primary and impersonation tokens, and why account changes don't reach running programs.
related:
  - peios/identity-and-access/security-identifiers
  - peios/identity-and-access/privileges
  - peios/identity-and-access/token
  - peios/local-accounts/sessions-and-account-changes
---

An access token is the identity a running program acts with. Each thread in a
program carries one, and every time the thread opens a file, reads a registry
key, or sends a signal, Peios checks the request against that token. The
token, not the account name a program displays, decides what the program can
do.

## What a token holds

A token holds the facts Peios needs to decide a request:

- **The user.** The security identifier (SID) of the principal the token
  represents.
- **Groups.** The SIDs of the groups the principal belongs to, and the logon
  SID of its [logon session](~peios/identity-and-access/logon-sessions).
- **Privileges.** The system operations the principal can perform. See
  [Privileges](~peios/identity-and-access/privileges).
- **An integrity level.** A level of trust that limits what the token can
  change. See [Integrity Levels](~peios/identity-and-access/integrity-levels).
- **Defaults for new objects.** The owner and permissions that objects the
  program creates receive.

Some of these fields can be adjusted while the token is in use. A program can
turn one of its privileges on or off, or turn a group off. The identity
fields, such as the user, the set of groups, and the integrity level, can't be
changed after the token is created.

To see the token a program is using, run `token show`. See
[Inspecting Effective Identity](~peios/identity-and-access/token).

## How a program gets a token

A program can copy its token or make a weaker version of it, but creating a
token for an identity is reserved for the kernel and two trusted programs,
authd and peinit. Tokens come from three places:

- **At boot,** the kernel creates the token for the operating system's own
  identity, Local System. The service manager, peinit, starts with it.
- **At sign-in,** authd, the authentication service, checks your credentials
  against policy and creates a token for you. The program you signed in
  through, such as the console or the desktop, starts your session with it.
- **For a service,** peinit gives the service's first program the token for
  the service's account.

After that, a new program inherits a copy of its parent's token. Running
another program file keeps the same token, unless the file is marked to run
at a lower integrity level. So everything started from your desktop or your
shell runs with the identity you signed in with.

## Primary and impersonation tokens

A program's own token is its primary token, and its threads share it. A
thread can also take on another token for a while, which is called
impersonation. A service uses impersonation to act for a client: it handles
the client's request with the client's identity, so the request can do only
what the client could do. When the thread stops impersonating, it returns to
the primary token.

A new program never inherits impersonation. It starts with its parent's
primary token.

## Account changes and running programs

A token records the account as it was when the token was created. Changing an
account afterward, for example adding it to a group, disabling it, or
changing its privileges, doesn't change tokens that already exist. Programs
already running keep their previous access.

To pick up a change, start a new sign-in. To stop a running session, end it:
[Inspecting and Ending Sessions](~peios/local-accounts/logonse) covers the
command and what it reaches.

The kernel's [token model](~kernel/internals/kacs/tokens/the-token-model)
describes every field and operation.

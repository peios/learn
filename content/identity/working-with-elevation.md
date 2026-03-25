---
title: Working with Elevation
type: how-to
order: 150
---

Use `idn` to check elevation status and request elevation when administrative access is needed.

## Check whether the current session is elevated

```
$ idn elevation
Status:    filtered
Integrity: Medium
```

This tells you the session is running with the filtered token — standard-user permissions. Administrative groups are present but set to deny-only.

When elevated:

```
$ idn elevation
Status:    elevated
Integrity: High
```

## Check another process

```
$ idn elevation --pid 2087
Status:    elevated
Integrity: High
```

## Request elevation

To launch a process with the elevated token:

```
$ elevate dbadmin --repair /srv/data/accounts.db
```

The system prompts through the trusted credential path — a secure channel that cannot be intercepted by other processes. After confirmation, the process launches with the full elevated token: all groups active, all assigned privileges present, High integrity level.

## Run a shell with elevation

```
$ elevate sh
```

This opens an elevated shell. All commands within it run with the elevated token. Exit the shell to return to the filtered session.

## Verify elevation from inside a process

A process can check its own elevation state:

```
$ idn elevation
Status:    elevated
Integrity: High
```

Or check whether specific groups are active (not deny-only):

```
$ idn groups
SID                                      Name                 State
S-1-5-32-544                             Administrators       enabled
S-1-5-21-...-512                         Domain Admins        enabled
S-1-5-21-...-513                         Domain Users         enabled
```

If Administrators shows `enabled` rather than `deny-only`, the token is elevated.

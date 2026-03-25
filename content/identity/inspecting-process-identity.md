---
title: Inspecting a Process's Identity
type: how-to
order: 110
---

Use `idn show` to inspect the token attached to a process.

## Show the current process's token

Running `idn show` with no arguments displays the token of the calling process:

```
$ idn show
User:         S-1-5-21-3623811015-3361044348-30300820-1013 (alice)
Integrity:    Medium
Logon Session: 47291 (Interactive)
Primary:      yes

Groups:
  S-1-5-21-...-513       Domain Users         enabled
  S-1-5-32-545           Users                enabled
  S-1-5-5-0-47291        Logon SID            enabled

Privileges:
  SeChangeNotifyPrivilege                      enabled
  SeShutdownPrivilege                          disabled
```

Each section shows a key part of the token:

- **User** — the SID and name of the principal this token represents
- **Integrity** — the token's trust tier
- **Logon Session** — the session ID and logon type
- **Primary** — whether this is the process's primary token (as opposed to an impersonation token on the calling thread)
- **Groups** — every group SID in the token, with its current state
- **Privileges** — every privilege in the token, with its enabled or disabled state

## Show another process's token

Pass a PID to inspect a different process:

```
$ idn show 1482
User:         S-1-5-19 (Local Service)
Integrity:    System
Logon Session: 3 (Service)
Primary:      yes

Groups:
  S-1-5-32-545           Users                enabled
  S-1-5-80-2739571183    DNS Service          enabled

Privileges:
  SeBindPrivilegedPortPrivilege                enabled
  SeChangeNotifyPrivilege                      enabled
```

Inspecting another process's token requires sufficient access to that process. If your token does not grant the necessary rights on the target process's security descriptor, the request is denied.

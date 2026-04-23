---
title: Inspecting a Thread's Impersonation State
type: how-to
description: How to check whether a thread is impersonating and inspect its impersonation token with idn show.
---

Use `idn show` with a thread specifier to check whether a thread is impersonating and inspect the impersonation token it carries.

## Check a thread's impersonation state

Specify a thread with `pid/tid`:

```bash
$ idn show 1482/1509
User:            S-1-5-21-3623811015-3361044348-30300820-1013 (alice)
Integrity:       Medium
Logon Session:   47291 (Interactive)
Impersonating:   yes
Impersonation Level: Impersonation

Groups:
  S-1-5-21-...-513       Domain Users         enabled
  S-1-5-32-545           Users                enabled
  S-1-5-5-0-47291        Logon SID            enabled

Privileges:
  SeChangeNotifyPrivilege                      enabled
```

The key differences from a primary token display:

- **Impersonating** — `yes` indicates this thread is carrying an impersonation token
- **Impersonation Level** — how far this token's identity can travel (Anonymous, Identification, Impersonation, or Delegation)

In this example, a service thread (in process 1482) is impersonating Alice at the Impersonation level — it can act as Alice for local operations.

## When a thread is not impersonating

If the thread is using the process's primary token, the output says so:

```bash
$ idn show 1482/1485
User:            S-1-5-19 (Local Service)
Integrity:       System
Logon Session:   3 (Service)
Impersonating:   no

Groups:
  S-1-5-32-545           Users                enabled
  S-1-5-80-2739571183    DNS Service          enabled

Privileges:
  SeBindPrivilegedPortPrivilege                enabled
  SeChangeNotifyPrivilege                      enabled
```

This thread is running with the process's primary token — the service's own identity.

## Listing threads in a process

To see all threads in a process and their impersonation state at a glance:

```bash
$ idn threads 1482
TID     Impersonating   User
1482    no              S-1-5-19 (Local Service)
1485    no              S-1-5-19 (Local Service)
1509    yes             S-1-5-21-...-1013 (alice)
1510    yes             S-1-5-21-...-1028 (bob)
1511    no              S-1-5-19 (Local Service)
```

This shows the service handling requests for two clients (Alice and Bob) on dedicated threads, while the remaining threads run under the service's own identity.

---
title: Comparing Two Tokens
type: how-to
order: 140
---

Use `idn compare` to see what two tokens have in common and where they differ. This is useful for troubleshooting — understanding why two processes have different access when you expect them to behave the same.

## Compare two processes

```
$ idn compare 2041 2087
                         PID 2041                PID 2087
User SID:                S-1-5-21-...-1013       S-1-5-21-...-1013
                         (alice)                 (alice)                  =
Integrity:               Medium                  High                     !=
Logon Session:           47291                   47291                    =

Groups:
  S-1-5-21-...-512       deny-only               enabled                  !=
  S-1-5-21-...-513       enabled                 enabled                  =
  S-1-5-32-544           deny-only               enabled                  !=
  S-1-5-32-545           enabled                 enabled                  =
  S-1-5-5-0-47291        enabled                 enabled                  =

Privileges:
  SeChangeNotifyPrivilege       enabled           enabled                  =
  SeShutdownPrivilege           -                 disabled                 !=
  SeTakeOwnershipPrivilege      -                 disabled                 !=
  SeBackupPrivilege             -                 enabled                  !=
```

The `=` and `!=` markers highlight what matches and what differs. A `-` indicates the privilege or group is not present in that token.

In this example, both processes belong to Alice and share the same logon session — but PID 2041 is her filtered token (administrative groups set to deny-only, fewer privileges) and PID 2087 is her elevated token (full group memberships, additional privileges, higher integrity level).

## Compare a thread's impersonation token against the primary

Use `pid/tid` syntax to compare a thread's impersonation token with the process's primary token:

```
$ idn compare 1482 1482/1509
                         PID 1482                TID 1509
User SID:                S-1-5-19                S-1-5-21-...-1013
                         (Local Service)         (alice)                  !=
Integrity:               System                  Medium                   !=
Logon Session:           3                       47291                    !=

Groups:
  S-1-5-21-...-513       -                       enabled                  !=
  S-1-5-32-545           enabled                 enabled                  =
  S-1-5-80-2739571183    enabled                 -                        !=
  S-1-5-5-0-47291        -                       enabled                  !=

Privileges:
  SeBindPrivilegedPortPrivilege enabled           -                        !=
  SeChangeNotifyPrivilege       enabled           enabled                  =
```

This shows a service (Local Service) with one thread impersonating Alice. The tokens are completely different identities — different user SIDs, different groups, different privileges — which is exactly what impersonation is designed to do.

## Structured output

For scripting, `--json` outputs the comparison as structured data:

```
$ idn compare --json 2041 2087
```

Each field includes both values and whether they match, making it straightforward to filter for differences.

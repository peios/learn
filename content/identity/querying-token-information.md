---
title: Querying Token Information (SIDs, Groups, Privileges)
type: how-to
order: 130
---

The `idn` tool provides focused subcommands for querying specific parts of a token. These are useful for quick checks and scripting where the full `idn show` output is more than you need.

## Query the user SID

```
$ idn sid
S-1-5-21-3623811015-3361044348-30300820-1013 (alice)

$ idn sid 1482
S-1-5-19 (Local Service)
```

Returns the token's user SID and resolved name. With no arguments, queries the current process. Pass a PID to query another process.

## Query group memberships

```
$ idn groups
SID                                      Name                 State
S-1-5-21-...-513                         Domain Users         enabled
S-1-5-32-545                             Users                enabled
S-1-5-5-0-47291                          Logon SID            enabled
```

Each group shows its current state:

| State | Meaning |
|---|---|
| **enabled** | The group is active and will match allow rules |
| **mandatory** | The group is always active and cannot be disabled |
| **deny-only** | The group can match deny rules but not allow rules |
| **disabled** | The group is present but currently inactive |

Query another process's groups by passing a PID:

```
$ idn groups 1482
SID                                      Name                 State
S-1-5-32-545                             Users                enabled
S-1-5-80-2739571183                      DNS Service          enabled
```

## Query privileges

```
$ idn privileges
Privilege                                State
SeChangeNotifyPrivilege                  enabled
SeShutdownPrivilege                      disabled
SeIncreaseBasePriorityPrivilege          disabled
```

To see only the privileges that are currently enabled:

```
$ idn privileges --enabled
Privilege                                State
SeChangeNotifyPrivilege                  enabled
```

Query another process's privileges by passing a PID:

```
$ idn privileges 1482
Privilege                                State
SeBindPrivilegedPortPrivilege            enabled
SeChangeNotifyPrivilege                  enabled
```

## Scripting

All `idn` subcommands support `--json` for structured output:

```
$ idn groups --json
[
  {"sid": "S-1-5-21-...-513", "name": "Domain Users", "state": "enabled"},
  {"sid": "S-1-5-32-545", "name": "Users", "state": "enabled"},
  {"sid": "S-1-5-5-0-47291", "name": "Logon SID", "state": "enabled"}
]
```

This makes it straightforward to filter and process token information in scripts and automation.

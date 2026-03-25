---
title: Managing Privileges
type: how-to
order: 110
---

Use `idn` to enable, disable, and remove privileges on your token.

## Enable a privilege

```
$ idn privilege enable SeShutdownPrivilege
SeShutdownPrivilege: disabled -> enabled
```

The privilege must already be present on the token. You cannot enable a privilege that was not assigned at token creation.

## Disable a privilege

```
$ idn privilege disable SeShutdownPrivilege
SeShutdownPrivilege: enabled -> disabled
```

A disabled privilege is still present on the token — it can be re-enabled later. Disabling a privilege you are not actively using reduces the impact of a compromise.

## Permanently remove a privilege

```
$ idn privilege remove SeShutdownPrivilege
SeShutdownPrivilege: removed (permanent)
```

Removal is irreversible. The privilege is gone from the token and cannot be re-enabled. This is useful for processes that need a privilege during initialization but should not carry it afterward — enable it, do the work, then remove it.

## Enable or disable multiple privileges

```
$ idn privilege enable SeBackupPrivilege SeRestorePrivilege
SeBackupPrivilege:  disabled -> enabled
SeRestorePrivilege: disabled -> enabled
```

## Manage privileges on another process

Pass a PID to manage privileges on another process's token, if your token grants sufficient access:

```
$ idn privilege enable SeShutdownPrivilege --pid 2041
SeShutdownPrivilege: disabled -> enabled (PID 2041)
```

## Verify the current state

```
$ idn privileges
Privilege                                State
SeChangeNotifyPrivilege                  enabled
SeShutdownPrivilege                      disabled
SeBackupPrivilege                        disabled
SeRestorePrivilege                       disabled
```

Or filter to see only what is currently active:

```
$ idn privileges --enabled
Privilege                                State
SeChangeNotifyPrivilege                  enabled
```

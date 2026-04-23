---
title: Managing Privileges
type: how-to
description: Enabling, disabling, and permanently removing privileges on a token using the idn tool.
---

Use `idn` to enable, disable, and remove privileges on your token.

## Enable a privilege

```bash
$ idn privilege enable SeShutdownPrivilege
SeShutdownPrivilege: disabled -> enabled
```

The privilege must already be present on the token. You cannot enable a privilege that was not assigned at token creation.

## Disable a privilege

```bash
$ idn privilege disable SeShutdownPrivilege
SeShutdownPrivilege: enabled -> disabled
```

A disabled privilege is still present on the token — it can be re-enabled later. Disabling a privilege you are not actively using reduces the impact of a compromise.

## Permanently remove a privilege

```bash
$ idn privilege remove SeShutdownPrivilege
SeShutdownPrivilege: removed (permanent)
```

Removal is irreversible. The privilege is gone from the token and cannot be re-enabled. This is useful for processes that need a privilege during initialization but should not carry it afterward — enable it, do the work, then remove it.

## Enable or disable multiple privileges

```bash
$ idn privilege enable SeBackupPrivilege SeRestorePrivilege
SeBackupPrivilege:  disabled -> enabled
SeRestorePrivilege: disabled -> enabled
```

## Manage privileges on another process

Pass a PID to manage privileges on another process's token, if your token grants sufficient access:

```bash
$ idn privilege enable SeShutdownPrivilege --pid 2041
SeShutdownPrivilege: disabled -> enabled (PID 2041)
```

## Verify the current state

```bash
$ idn privileges
Privilege                                State
SeChangeNotifyPrivilege                  enabled
SeShutdownPrivilege                      disabled
SeBackupPrivilege                        disabled
SeRestorePrivilege                       disabled
```

Or filter to see only what is currently active:

```bash
$ idn privileges --enabled
Privilege                                State
SeChangeNotifyPrivilege                  enabled
```

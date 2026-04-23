---
title: Creating Restricted Tokens
type: how-to
description: Using idn filter to create restricted tokens with deny-only groups, removed privileges, and restricting SIDs.
---

Use `idn filter` to create a restricted copy of an existing token with fewer privileges, deny-only groups, or restricting SIDs.

## Remove privileges

Strip specific privileges from the new token:

```bash
$ idn filter --remove-privilege SeShutdownPrivilege --remove-privilege SeDebugPrivilege
```

The removed privileges are gone permanently — they cannot be re-enabled on the new token.

## Set groups to deny-only

Convert groups so they can match deny ACEs but not allow ACEs:

```bash
$ idn filter --deny-only Administrators --deny-only "Domain Admins"
```

The groups remain visible on the token but cannot grant access. This is the mechanism used to create filtered tokens for linked token pairs.

## Add restricting SIDs

Create a dual-evaluation constraint by adding restricting SIDs:

```bash
$ idn filter --restrict "read-only-workers" --restrict "app-sandbox"
```

The resulting token requires both the normal and restricted DACL evaluations to agree before access is granted.

## Prevent child process creation

Block the process from spawning children:

```bash
$ idn filter --no-child-process
```

This is useful for sandboxing — a confined or restricted process that cannot create children cannot escape its constraints by launching a less-restricted process.

## Combine operations

Multiple restrictions can be applied in a single operation:

```bash
$ idn filter \
    --deny-only Administrators \
    --remove-privilege SeDebugPrivilege \
    --remove-privilege SeShutdownPrivilege \
    --restrict "app-sandbox" \
    --no-child-process
```

This creates a token with administrative groups set to deny-only, two privileges removed, a restricting SID added, and child process creation blocked.

## Apply to another process

By default, `idn filter` creates a filtered copy of the current process's token and installs it. To filter and install on a specific process:

```bash
$ idn filter --pid 4012 --deny-only Administrators
```

This requires appropriate access to the target process.

## Verify the result

Inspect the filtered token to confirm the restrictions:

```bash
$ idn show 4012
User:         S-1-5-21-...-1013 (alice)
Integrity:    Medium
Restricted:   yes

Groups:
  S-1-5-32-544           Administrators       deny-only
  S-1-5-21-...-513       Domain Users         enabled

Restricting SIDs:
  app-sandbox

Privileges:
  SeChangeNotifyPrivilege                      enabled

No child process: yes
```

The token shows the deny-only group, the restricting SID, the reduced privilege set, and the child process restriction.

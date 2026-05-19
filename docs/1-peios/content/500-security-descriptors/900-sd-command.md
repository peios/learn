---
title: The sd command
type: reference
description: sd is the command-line tool for reading and changing the security descriptor on a file — its owner, its access rules, its audit rules, its integrity label, and its inheritance.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/ownership
  - peios/security-descriptors/inheritance
  - peios/access-decisions/overview
---

`sd` is the command-line tool for working with **security descriptors** on files. Everything this topic describes — owners, DACLs, ACEs, the SACL, integrity labels, inheritance — `sd` is how you read it and change it from a shell.

```
sd subcommand path [arguments]
```

```
$ sd show ./report.txt
$ sd allow ./report.txt alice:read
$ sd owner ./report.txt BA
```

Where [`ls -l`](~peios/listing-and-paths/ls) shows a file's owner and a summary, and [`cp --preserve`](~peios/files-and-directories/cp) carries a descriptor across, `sd` is the tool that *edits* the descriptor directly.

## The subcommands

| Group | Subcommand | Does |
|---|---|---|
| Inspect | `show` | Print the descriptor on a path. |
| | `check` | Simulate an access check against the path. |
| DACL | `allow` | Add an allow rule for one or more principals. |
| | `deny` | Add a deny rule for one or more principals. |
| | `remove` | Drop every DACL rule for the named principals. |
| Auditing | `audit` | Add an audit rule to the SACL. |
| | `unaudit` | Drop every SACL rule for the named principals. |
| Ownership | `owner` | Set the descriptor's owner. |
| | `group` | Set the descriptor's group. |
| Integrity | `integrity` | Set the mandatory integrity label. |
| Inheritance | `inherit` | Turn inheritance protection on or off. |
| | `reset` | Drop the file's own rules and re-inherit from the parent. |
| | `propagate` | Push inheritance down to descendants. |
| Wholesale | `set` | Replace the entire descriptor at once. |

## Naming a principal

Wherever a subcommand takes a `PRINCIPAL`, it accepts any of:

| Form | Example | Meaning |
|---|---|---|
| `@self` | `@self` | The user SID of the token running `sd`. |
| `@owner` | `@owner` | A placeholder that the access check substitutes with the file's own owner. |
| A well-known label | `Everyone`, `Administrators`, `LocalSystem` | A named built-in principal. |
| A two-letter alias | `WD`, `BA`, `SY` | The short alias for a well-known principal. |
| A raw SID | `S-1-5-32-544` | Any SID, written out in full. |

See [SIDs](~peios/identity/sids) for what these are.

## Naming permissions

Wherever a subcommand takes `PERMS`, several notations are accepted, and may be mixed:

| Form | Example | Meaning |
|---|---|---|
| Single letters | `rwx`, `r`, `m` | `r` read, `w` write, `x` execute, `d` delete, `m` modify, `f` full, `c` change-permissions, `o` take-ownership. |
| Words | `read,write`, `modify` | The same set, spelled out. |
| Fine-grained names | `read-data,append,traverse` | Individual low-level rights, for precise rules. |
| Raw hex | `0x1F01FF` | An access mask written directly. |

Run letters together (`rwx`) or separate names with commas (`read,write,execute`).

## Inspecting

### `sd show`

Prints the descriptor on a path — the owner, the group, the DACL, the SACL.

```
$ sd show ./report.txt
```

| Flag | Effect |
|---|---|
| `--sddl` | Render the descriptor as an SDDL string. |
| `--raw` | Render SIDs in raw `S-1-…` form only. |
| `--label` | Render SIDs as their labels where known. |
| `--all` | Verbose — decode every flag and show raw masks alongside. |
| `--json` | Emit JSON. |

### `sd check`

Simulates an [access decision](~peios/access-decisions/overview): "would this access be allowed?" — without performing it.

```
$ sd check ./report.txt write
$ sd check ./report.txt read --pid 4821 --explain
```

| Argument / flag | Effect |
|---|---|
| `PERMS` | The access to test for. |
| `--pid PID` | Check against process `PID`'s token instead of your own. |
| `--explain` | Show *why* the decision came out as it did — the rule-by-rule walk. |

`sd check` is the first thing to reach for when an access is denied and you do not know why. `--explain` walks the descriptor the same way the kernel does.

## Changing the DACL

The DACL is the list of allow and deny rules. These three subcommands edit it.

### `sd allow` and `sd deny`

Add an allow (or deny) rule for one or more `PRINCIPAL:PERMS` pairs.

```
$ sd allow ./report.txt alice:read bob:rw
$ sd deny  ./report.txt Everyone:write
```

| Flag | Effect |
|---|---|
| `--flags LIST` | ACE inheritance flags — `CI` container-inherit, `OI` object-inherit, `NP` no-propagate, `IO` inherit-only; `none` clears them. |
| `--if EXPR` | Make it a [conditional rule](~peios/security-descriptors/conditional-aces), applied only when `EXPR` is true. |
| `--replace` | Drop any existing rules for this principal and kind first, instead of appending. |
| `--recursive`, `-r` | Apply to every descendant of the path. |

Remember that a **deny** rule, when it matches, wins over any allow — see [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

### `sd remove`

Drops *every* DACL rule — allow and deny — for the named principals.

```
$ sd remove ./report.txt bob carol
```

| Flag | Effect |
|---|---|
| `--allow-empty` | Permit the result to be a present-but-empty DACL, which denies everyone. Without this, `sd` refuses to produce one. |
| `--recursive`, `-r` | Apply to every descendant. |

## Auditing

### `sd audit` and `sd unaudit`

The SACL holds audit rules — see [The SACL](~peios/security-descriptors/the-sacl). `sd audit` adds one; `sd unaudit` drops every SACL rule for the named principals.

```
$ sd audit ./secrets.db Everyone:write:failure
```

An audit spec is `PRINCIPAL:PERMS:WHEN`, where `WHEN` is `success`, `failure`, or `both` — which outcomes to log. `sd audit` takes the same `--flags`, `--if`, `--replace`, and `-r` options as `sd allow`.

## Ownership

### `sd owner` and `sd group`

Set the descriptor's owner or group SID.

```
$ sd owner ./report.txt alice
$ sd group ./report.txt Administrators
```

Both take a single `PRINCIPAL` and accept `-r`. Changing an owner is itself an access-controlled act — see [Ownership](~peios/security-descriptors/ownership).

## Integrity

### `sd integrity`

Sets the file's mandatory integrity label.

```
$ sd integrity ./report.txt high
```

The level is one of `untrusted`, `low`, `medium`, `medium-plus`, `high`, `system`, `protected`.

| Flag | Effect |
|---|---|
| `--policy BITS` | The label's policy bits, comma-separated: `NW` no write-up, `NR` no read-up, `NX` no execute-up. |
| `--recursive`, `-r` | Apply to every descendant. |

For what the label does, see [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).

## Inheritance

### `sd inherit`

Turns inheritance protection on or off — the `+` mark `ls -l` shows.

```
$ sd inherit off ./report.txt    # lock the file; stop inheriting
$ sd inherit on  ./report.txt    # let it inherit from its parent again
```

`inherit on` lets the file inherit rules from its parent directory. `inherit off` *protects* the file — it keeps its current rules and stops tracking the parent.

| Flag | Effect |
|---|---|
| `--strip-inherited` | When turning protection off, also drop the inherited rules already on the file. |
| `--recursive`, `-r` | Apply to every descendant. |

### `sd reset`

Drops the file's own explicit rules and rebuilds its DACL purely from what the parent directory hands down — returning the file to "inherits everything".

### `sd propagate`

Pushes this directory's inheritable rules down into its descendants, refreshing what they inherit. Use it after changing a directory's rules so the children pick up the change.

See [Inheritance](~peios/security-descriptors/inheritance) for the full model.

## Replacing the whole descriptor

### `sd set`

Replaces the entire descriptor in one step.

```
$ sd set ./report.txt 'O:BAG:BAD:P(A;;FA;;;BA)(A;;0x1200a9;;;BU)'
```

| Argument / flag | Effect |
|---|---|
| `SDDL` | The new descriptor as an SDDL string. `-` reads it from standard input. |
| `--binary FILE` | Instead of SDDL, read the raw descriptor bytes from `FILE` (`-` for standard input). |
| `--components LIST` | Override which parts of the descriptor (owner, group, DACL, SACL) the operation writes. |

## Common flags

These apply across the subcommands:

| Flag | Effect |
|---|---|
| `--recursive`, `-r` | Apply the change to every descendant of the path. |
| `--no-follow-symlinks`, `-P` | Operate on a symbolic link itself, not the file it points to. |
| `--json` | Emit JSON instead of human-readable output. |

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — or, for `sd check`, the access would be **allowed**. |
| non-zero | The operation failed, the path was unreachable, or — for `sd check` — the access would be **denied**. |

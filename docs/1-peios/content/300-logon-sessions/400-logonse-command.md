---
title: The logonse command
type: reference
description: logonse is the command-line tool for logon sessions — listing them, seeing which processes belong to one, creating and destroying them, and setting a process's mitigation flags.
related:
  - peios/logon-sessions/overview
  - peios/logon-sessions/lifecycle
  - peios/inspecting/sessions
  - peios/process-mitigations/overview
---

`logonse` is the command-line tool for **logon sessions** — the kernel's records of authentication events that this topic describes. It lists the active sessions, shows which processes belong to one, creates and destroys sessions, and (as a related low-level job) sets a process's mitigation flags.

```
logonse subcommand [arguments]
```

```
$ logonse list
$ logonse show 4711
```

`logonse` is a low-level administrative and debugging tool. A session subcommand requires one — `list`, `show`, `create`, `destroy`, or `psb`.

## Listing sessions

### `logonse list`

Enumerates the active logon sessions, and the process IDs in each.

```
$ logonse list
session 0     pids: [1, 2, 14, 22]
session 4711  pids: [820, 844, 901]
```

### `logonse show`

Shows the process IDs that belong to one session.

```
$ logonse show 4711
```

### A caveat on list and show

There is no single kernel call that enumerates logon sessions. `logonse list` and `logonse show` work by walking the running processes and reading each one's token to find which session it belongs to. That has two consequences worth knowing:

- It is **best-effort**. A session that has no running process — held alive only by a token file descriptor somewhere — will not appear, because there is no process to find it through.
- It is a **snapshot under change**. Processes start and exit while the walk runs, so the result is a close approximation of the moment, not a locked one.

For routine "who is signed in" use this is fine. For an authoritative listing, the kernel's own sessions surface — described in [Inspecting sessions](~peios/inspecting/sessions) — is the source of record.

## Creating and destroying sessions

### `logonse create`

Creates a new logon session from a binary specification.

```
$ logonse create session-spec.bin
```

`SPEC` is a file, or `-` to read the specification from standard input. On success `logonse` prints the new session's id. Creating a session is a **privileged** operation — minting authentication records is reserved for the components that legitimately do so.

### `logonse destroy`

Destroys a session — but only an **empty** one, with no tokens still referencing it.

```
$ logonse destroy 4711
```

A session with live tokens cannot be destroyed this way; its tokens must go first. See [Session lifecycle](~peios/logon-sessions/lifecycle).

## Setting process mitigation flags

### `logonse psb`

`logonse psb` sets the **mitigation flags** in a process's Process Security Block.

```
$ logonse psb --pid 4821 --mitigations 0x1c0
```

| Flag | Meaning |
|---|---|
| `--pid PID` | The process to act on. |
| `--mitigations MASK` | The mitigation bitmask to apply, in hexadecimal or decimal. |

This subcommand is about process hardening rather than logon sessions — it lives in `logonse` because both deal with low-level per-process kernel state. For what the mitigation flags mean and how they behave, see [Process mitigations](~peios/process-mitigations/overview).

## Output options

| Flag | Effect |
|---|---|
| `--json` | Emit JSON instead of human-readable output. Accepted by every subcommand. |

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded. |
| `1` | A usage error, or the operation failed. |

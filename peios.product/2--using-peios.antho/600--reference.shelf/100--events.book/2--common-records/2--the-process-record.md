---
title: The Process Record
description: The process map identifying where an event came from, what to correlate on, and why there is no thread ID.
---

The `process` map identifies the process the event came from. It appears
in every KACS event except `logon-session-destroyed`, which has no
causing process.

| Key | Type | Meaning |
|---|---|---|
| `pid` | uint | The process ID. |
| `name` | string | The kernel's name for the process, typically the executable's basename. |
| `executable_path` | string | The path resolved at exec, with symlinks already followed. |

Every field is always present. For `continuous-audit` this is the
operation-time process, not the one that opened the handle.

## Correlating on it

`pid` is reliable only in the short term. Process IDs are reused, so a
`pid` in a week-old record may name something unrelated. For durable
records, correlate on `name` and `executable_path`.

`name` is the kernel's internal name. It is not `argv[0]`, and a process
that rewrote its argv is unaffected here.

## No thread ID

The record identifies a process, not a thread. Events that fire on one
specific thread still report only the process. Nothing in the current
event set carries a `tid`.

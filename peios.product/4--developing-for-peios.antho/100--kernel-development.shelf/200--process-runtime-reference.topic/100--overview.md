---
title: Process runtime reference
type: reference
description: Developer contracts for process creation, program replacement, termination, child collection, orphan adoption, and per-thread operations.
related:
  - peios/developing-for-peios/process-runtime-reference/process-creation-reference
  - peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference
  - peios/developing-for-peios/process-runtime-reference/thread-operations-reference
  - peios/threads-and-processes/task-manager
---

Use this reference when implementing a launcher, supervisor, threading library,
or other code that creates and controls processes. For inspecting or stopping a
running program, start with [Task Manager](~peios/threads-and-processes/task-manager)
and [Process lifecycle](~peios/threads-and-processes/process-lifecycle).

- [Process creation](~peios/developing-for-peios/process-runtime-reference/process-creation-reference):
  `fork`, `vfork`, `clone`/`clone3`, sharing flags, `exec`, `posix_spawn`, and pidfds.
- [Process lifecycle](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference):
  termination, exit-status encoding, the wait family, and subreaper adoption.
- [Thread operations](~peios/developing-for-peios/process-runtime-reference/thread-operations-reference):
  TIDs, thread-exit notification, and thread-local storage.

These calls also interact with Peios security. See
[Token lifecycle](~peios/security-fundamentals/tokens/lifecycle) for identity
inheritance, [the process security descriptor](~peios/process-integrity-protection/the-process-security-descriptor)
for process rights, and [the two-check rule](~peios/process-integrity-protection/the-two-check-rule)
for cross-process access.

---
title: Thread operations reference
type: reference
description: Find the developer contracts for thread IDs, thread-exit notification and thread-local storage.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/developing-for-peios/process-runtime-reference/thread-operations-reference
---

For understanding a process's thread count and identifiers, read
[The process and thread model](~peios/threads-and-processes/the-process-and-thread-model).
The per-thread API contract now lives in the developer
[Thread operations reference](~peios/developing-for-peios/process-runtime-reference/thread-operations-reference).

## Thread IDs

A TID names a thread; a PID names the process. Neither identifies the principal
it acts as. The exact TID, PID, thread-group and library-handle distinctions
are in [Thread IDs](~peios/developing-for-peios/process-runtime-reference/thread-operations-reference#thread-ids).

## Thread-exit notification

Joining a thread uses notification when that thread ends. The clear-tid
address and wakeup contract are in
[Thread-exit notification](~peios/developing-for-peios/process-runtime-reference/thread-operations-reference#thread-exit-notification).

## Thread-local storage

Threads can keep their own values despite sharing process memory. The
kernel pointer, creation flag, architecture calls and library responsibilities
are in [Thread-local storage](~peios/developing-for-peios/process-runtime-reference/thread-operations-reference#thread-local-storage).

## See also

- [The process and thread model](~peios/threads-and-processes/the-process-and-thread-model): interpreting a running process and its threads.
- [Process runtime reference](~peios/developing-for-peios/process-runtime-reference/overview): creation, lifecycle and thread API contracts.

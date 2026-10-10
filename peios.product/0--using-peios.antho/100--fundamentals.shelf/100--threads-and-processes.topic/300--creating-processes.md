---
title: Creating processes
type: concept
description: What starting a program changes in a process list, what a child inherits, and why a program change or a reused PID can be misleading.
related:
  - peios/threads-and-processes/task-manager
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/threads-and-processes/process-lifecycle
  - peios/security-fundamentals/tokens/lifecycle
  - peios/developing-for-peios/process-runtime-reference/process-creation-reference
---

Starting a command or application can create new processes. In
[Task Manager](~peios/threads-and-processes/task-manager), select one to see its
parent, command and service or job. A new process gets a new PID and Process
GUID, but a running process can also change the program it runs without
changing either identifier.

These two cases explain most changes you see in the process list. You do not
need to call the creation APIs to start an application from the launcher or
run a command in a terminal.

## Splitting: one process becomes two

A running process can create a near-copy of itself. The original is the
**parent**; the new process is its **child**. This is called **fork**.

The child gets private memory copied from the parent, copies of its open
resources, and the same identity. Changes to one process's private memory do
not change the other's. The child has its own PID and Process GUID, and some
per-process state starts fresh. Identity inheritance is covered in
[Token lifecycle](~peios/security-fundamentals/tokens/lifecycle); the precise
inheritance list is in the developer
[creation reference](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#fork).

## Replacing: same process, different program

A process can replace its current program with another, called **exec**. Its
PID and Process GUID stay the same, and it retains its identity; the previous
program's memory and code are replaced. A changed program name therefore does
not by itself mean a different process has taken over that PID.

For the identity rules, including programs marked to run as another principal,
see [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle). The exact
preserved and reset state is in
[The exec family](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#the-exec-family).

## Putting them together

Launching a new program commonly combines the two steps: create a child, then
replace the child's program. **Spawn** combines this pattern for callers.
Thread creation uses the same underlying creation mechanism with resources
shared instead of private; the general mechanism is called **clone**.

For operating the system, check the resulting process and what manages it.
If a service keeps creating replacement processes, inspect the service's
status and [supervision policy](~peios/services-and-jobs/supervision), rather
than repeatedly ending each new PID. API details belong in the developer
[process creation reference](~peios/developing-for-peios/process-runtime-reference/process-creation-reference).

## Getting hold of the new process

A PID can be reused after a process ends. Recheck the current name, command,
owner and service or job before signalling a PID from a terminal, especially
if it came from an old log or an earlier inspection.

Programs can hold a **pidfd**, a file-descriptor handle tied to one specific
process, obtained at creation or for a process that already exists. Unlike a
bare PID, that handle cannot later refer to a different process; it can be used
to wait for the process or signal it. Task Manager holds onto the process from
the moment you ask to end it, protecting that action against PID reuse.
For code that needs this guarantee, see
[Process handles](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#process-handles-the-pidfd-family).

## Where to go next

[Process lifecycle](~peios/threads-and-processes/process-lifecycle) explains
states, termination, and cleanup. If you are implementing a launcher or
threading library, use the developer
[Process runtime reference](~peios/developing-for-peios/process-runtime-reference/overview).

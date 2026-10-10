---
title: Process lifecycle reference
type: reference
description: Find the developer contracts for termination, exit status and child collection; use the lifecycle guide for safe process control.
related:
  - peios/threads-and-processes/process-lifecycle
  - peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference
---

For safely ending, suspending or resuming a running program, use
[Process lifecycle](~peios/threads-and-processes/process-lifecycle).
The complete termination and wait API contract is now in the developer
[Process lifecycle reference](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference).

## Ending a process

Orderly termination gives a program a chance to clean up; immediate termination
does not. The distinctions between library cleanup, ending one thread and
ending the whole process are in
[Ending a process](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference#ending-a-process).

## The exit status

The result distinguishes a normal exit code from termination by a signal.
The precise encoding and status macros are in
[The exit status](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference#the-exit-status).

## Collecting the result

A finished child remains a zombie until its result is collected. Developers
implementing a parent or supervisor should use
[Collecting the result](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference#collecting-the-result)
for wait variants, target selection, options and resource usage, and
[Orphan adoption and subreapers](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference#orphan-adoption-and-subreapers)
for orphan handling.

## See also

- [Process lifecycle](~peios/threads-and-processes/process-lifecycle): states, safe control, zombies and orphans.
- [Task Manager](~peios/threads-and-processes/task-manager): inspect the target and choose the scope of a stop.
- [Process runtime reference](~peios/developing-for-peios/process-runtime-reference/overview): the developer reference entry point.

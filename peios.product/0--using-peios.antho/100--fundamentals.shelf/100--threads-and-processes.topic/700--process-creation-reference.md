---
title: Process creation reference
type: reference
description: Find the developer contracts for process creation and program replacement; use Task Manager to inspect the running result.
related:
  - peios/threads-and-processes/task-manager
  - peios/threads-and-processes/creating-processes
  - peios/developing-for-peios/process-runtime-reference/process-creation-reference
---

The complete API contract now lives in the developer
[Process creation reference](~peios/developing-for-peios/process-runtime-reference/process-creation-reference).
For everyday use, [Creating processes](~peios/threads-and-processes/creating-processes)
explains what a new process means in the process list, and
[Task Manager](~peios/threads-and-processes/task-manager) shows the running result.

## fork

A child gets its own PID and Process GUID while starting with the parent's
identity. The full list of inherited and reset resources is in
[fork](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#fork).

## vfork

This specialised launch operation temporarily shares the parent's memory.
Its strict restrictions on what the child may do are in
[vfork](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#vfork).

## clone and clone3

These are the general process and thread creation APIs. Their arguments,
size-versioned structure and privileged ID requests are in
[clone and clone3](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#clone-and-clone3).

## clone sharing flags

Sharing choices determine whether creation makes another thread or a separate
process. The complete flag table, dependencies, thread-group rules and namespace
restrictions are in
[clone sharing flags](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#clone-sharing-flags).

## The exec family

A process can change programs without changing its PID or Process GUID.
The API variants are in
[The exec family](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#the-exec-family).

### What survives an exec

The process continues, but program state is replaced. The exact lists of
preserved, reset and discarded resources are in
[What survives an exec](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#what-survives-an-exec).

## posix_spawn

For developers launching a program, the combined create-and-replace operation
is described in
[posix_spawn](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#posix-spawn).

## Process handles (the pidfd family)

A handle keeps referring to one process even if its old PID is reused.
The creation, signalling and descriptor-duplication calls and their access
constraints are in
[Process handles](~peios/developing-for-peios/process-runtime-reference/process-creation-reference#process-handles-the-pidfd-family).

## See also

- [Creating processes](~peios/threads-and-processes/creating-processes): the operator's view of startup and PID reuse.
- [Process lifecycle](~peios/threads-and-processes/process-lifecycle): interpret states and stop or pause safely.
- [Process runtime reference](~peios/developing-for-peios/process-runtime-reference/overview): the developer reference entry point.

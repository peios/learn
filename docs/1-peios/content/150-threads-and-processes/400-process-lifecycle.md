---
title: Process lifecycle
type: concept
description: Every process is created, runs for a while, and then ends. This page covers how a process ends, how its result is collected, what happens when its parent ends first, and how the system cleans up after it.
related:
  - peios/threads-and-processes/creating-processes
  - peios/threads-and-processes/relationships-and-job-control
  - peios/tokens/lifecycle
---

Every process eventually ends. A process's life has three parts — it is
created, it runs, and it finishes — and the system ensures that when it
finishes, its result is collected and its resources are reclaimed.

## The states it passes through

While it exists, a process is in one of a handful of **states**, and the system
moves it between them. Most of the time it is either **running** — executing,
or ready to the moment a core is free — or **sleeping**, paused while it waits
for something to happen, such as data to arrive or a timer to fire. A sleeping
process uses no processor time until what it is waiting for is ready; most
processes spend most of their lives asleep.

A few states are worth knowing by name:

- **Stopped** — suspended (for example by job control when a job is paused at
  the terminal); it does nothing until told to resume.
- **Traced** — stopped under the control of a debugger that has attached to it, so
  the debugger can inspect and step it.
- **Uninterruptible sleep** — waiting on something the system will not interrupt,
  almost always a brief piece of disk or device I/O. A process here cannot be woken
  or even killed until the operation finishes; it normally lasts an instant, and a
  process stuck in it is a sign that hardware or a filesystem is wedged.
- **Zombie** — finished, but still held as a result waiting to be collected (see
  below).

Once its result has been collected the process is gone, removed from the system
entirely.

## Two ways a process ends

A process ends in one of two ways.

Most often it ends **on its own**: it finishes its work and stops. A process
that ends this way leaves behind an **exit status** — a small record of how it
went, usually just "succeeded" or "failed" (and, on failure, a number giving a
rough reason). The act of a process ending itself is called **exit**.

The other way is that a process is **stopped from outside** — something tells
it to stop, and it ends whether or not its work was done. (The messages that
do this are **signals**, a subject of their own.) A process ended this way
also leaves an exit status, marked to show it was stopped rather than
finishing on its own.

Either way, a record of the process remains until its result is collected.

## Collecting the result

Whenever a child changes state — ends, is stopped, or resumes — the system
sends its **parent** a signal, `SIGCHLD`, prompting it to check. The parent
then reads the child's exit status. This is called **waiting** for the
process. (`SIGCHLD` is an ordinary signal; signals as a mechanism are their
own subject.)

Between the moment a process ends and the moment its parent collects the
result, the finished process is a **zombie**: no longer running, but with the
system still holding its exit status so the parent can read it. Despite the
name, a zombie is harmless — it does no work and uses almost nothing; it is a
result waiting to be collected. The instant the parent collects it, the zombie
is gone for good.

If a parent never collects, zombies accumulate — finished processes whose
results no one read. That is a fault in the parent, not normal behaviour.

A parent holding a [pidfd](~peios/threads-and-processes/creating-processes) for its
child can wait on it directly — the dependable way to be told the exact moment the
child ends.

The exact calls — every `wait` variant, and how an exit status is read — are in the
[process lifecycle reference](~peios/threads-and-processes/process-lifecycle-reference).

## When the parent ends first

A parent does not always outlive its children. If a parent ends while one of
its children is still running, that child becomes an **orphan**.

Orphans are not lost, and nothing breaks. The system's first process — PID 1,
which on Peios is **peinit** — adopts every orphan and stands in as its parent
from then on: when the orphan eventually ends, peinit collects its result, so
no finished process is ever left uncollected. Adoption is automatic; the
orphan keeps running unaffected, only with a new parent.

PID 1 is the catch-all, but a process can arrange to catch orphans within its
own subtree. By marking itself a **subreaper** (with
`prctl(PR_SET_CHILD_SUBREAPER)`), a process becomes the one that adopts any
orphan descended from it — its grandchildren and below — instead of letting
them reparent all the way up to PID 1. Service managers and container managers
use this to keep responsibility for everything they launched: when something
deep in their subtree loses its immediate parent, it reparents to the manager,
which still learns when it finally ends.

## What the system cleans up

When a process ends, the system reclaims what it was using. Its private memory is
freed and its open files and connections are closed.

It also **releases its identity**. A process acts as a principal, carried on
its token; when the process ends, its hold on that token is released. If other
processes were sharing the same identity — siblings from the same login, say —
the identity lives on for them, and the system clears it away only once
nothing is using it any more. The details are in
[Token lifecycle](~peios/tokens/lifecycle).

The process's PID becomes available for the system to assign to a future
process. Its Process GUID is not reused — it remains a permanent marker of
that one process, so records of what it did still point unambiguously back to
it long after it is gone.

## Where to go next

Processes are arranged into a family tree and grouped together in ways that
matter for running them. That is
[Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control).

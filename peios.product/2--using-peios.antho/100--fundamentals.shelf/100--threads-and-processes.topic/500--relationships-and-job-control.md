---
title: Process relationships and job control
type: concept
description: The two ways processes relate — descent, forming a family tree rooted at PID 1, and grouping into process groups and sessions for job control.
related:
  - peios/threads-and-processes/process-lifecycle
  - peios/threads-and-processes/the-process-security-block
  - peios/logon-sessions/overview
---

Every process is related to others in two different ways: by **descent** — who
started whom — and by **grouping** — which processes are handled together when
they are controlled at a terminal.

## The family tree

Every process was started by another, so every process has a **parent**: the
process that created it. A process can refer to its parent by the parent's PID,
sometimes called the **PPID** (parent process ID).

Follow the parents upward and they all lead back to the same place — PID 1, the
first process, which the system starts at boot. Every other process descends from
it, directly or through a chain of parents, so the processes on a running system
form a single **family tree** rooted at PID 1. This is the same tree that makes
orphan adoption work: when a process loses its parent, PID 1 takes over the role,
[as covered in the lifecycle](~peios/threads-and-processes/process-lifecycle).

A few processes at the very root of the tree are special. **PID 1** is the first
process started at boot — on Peios, peinit — and the ancestor of all the rest; the
system protects it, refusing to kill it with any signal it has not chosen to handle,
because losing it would bring down the whole tree. Beneath the userspace processes
the kernel runs threads of its own: **PID 0** is the idle process (what a core runs
when it has nothing else to do), and **PID 2**, `kthreadd`, is the parent of every
kernel thread. The kernel's threads — among them the worker threads (`kworker`)
that run deferred work and the threads that service hardware interrupts — appear in
a process listing as the system's own work rather than as programs loaded from disk.

## Process groups

Several processes often do one job together. In a pipeline — the output of one
command feeding into the next — each command is its own process, but they form
one job: you stop, pause, or resume the whole job at once, not a piece at a
time.

To make that possible, related processes are collected into a **process group**.
A process group is a set of processes treated as a unit, so that an action — most
often a signal, like the one that stops a job — can be delivered to all of them
together instead of one by one.

## Sessions and the terminal

Process groups are themselves collected into a larger unit: a **session**, tied
to the **terminal** the work is running at.

A terminal can only take input for one job at a time, so within the session one
process group is the **foreground** group: the one connected to the keyboard, the
one typing reaches, the one a stop-or-interrupt keystroke acts on. Any other
groups are in the **background**, running without holding the keyboard. Moving a
job between foreground and background — and starting, stopping, and resuming jobs
— is **job control**.

## A different kind of "session"

The word "session" has two meanings here, and they are unrelated:

- A **job-control session**, described above, organises processes at a terminal
  — which groups share a terminal, which one is in the foreground. It says
  nothing about who anyone is.
- A **logon session** records one sign-in — a single authentication event — and
  ties together every identity token that came from it. It is part of the
  identity model, covered in [Logon sessions](~peios/logon-sessions/overview).

They often line up in practice — signing in at a terminal creates a logon session,
and the processes run there share a job-control session — but they are separate
things answering separate questions: "which processes share this terminal?" versus
"where did this identity come from?"

## Where to go next

Beyond its place in the tree and its groups, every process carries a bundle of its
security-related settings — its Process Security Block. That is
[The Process Security Block](~peios/threads-and-processes/the-process-security-block).

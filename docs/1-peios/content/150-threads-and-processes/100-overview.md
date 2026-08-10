---
title: Threads and processes
type: concept
description: A process is a running program; a thread is a single line of execution inside it. Every action the system takes happens on some thread. This page introduces both.
related:
  - peios/identity/overview
  - peios/tokens/overview
  - peios/confinement/overview
---

A **process** is a program that is running. When a program starts, the system
gives it a block of private memory that only it can see, a table of the files
and other resources it holds open, and a name the system tracks it by. That
running program, plus everything the system keeps for it, is a process. When
the program finishes, its process goes away.

A process can also do several things at once by running more than one
**thread**. A thread is a single line of execution — one sequence of steps the
system is working through. A process always has at least one thread (its
initial execution is its first thread), and it can start more. Every thread in
a process shares the same private memory and the same open resources. What
each thread keeps to itself is its own place in its sequence: each runs its
own steps, at its own pace, possibly in parallel with the others.

## The actors of the system

Processes and threads are what carry out work on the system. Every action —
opening a file, sending data over a network, starting another program — is
performed by some thread. When the system decides whether an action is
allowed, the question it answers is "is this thread allowed?" When it records
that something happened, it records which thread did it.

A thread always acts as someone — a person, a service, or the system itself.
Peios carries that identity along with the thread on a small object called a
**token** (see [Tokens](~peios/tokens/overview)). Two facts matter here:

- Every thread is always acting as someone. There is no "nobody" state.
- When one process starts another, the new process begins acting as the same
  identity as the process that started it.

## What a process has

The things the system keeps for every process:

| It has | Which means |
|---|---|
| Private memory | working space only this process can see; other processes cannot read it |
| Open resources | the files, connections, and other things it currently holds open |
| An identity | who it is acting as (carried on its token) |
| A place in a family tree | every process was started by another, so processes form a tree |
| A lifecycle | it is created, it runs, and it ends — and its end is always observed |
| One or more threads | the lines of execution doing its work |

This is not the full list — a process also carries other per-process state,
such as its **Process Security Block** (PSB), which holds its security-related
settings and comes up further on.

## Where to go next

Continue with [The process and thread model](~peios/threads-and-processes/the-process-and-thread-model)
for how a thread and a process relate, and why the thread — not the process —
is the more basic unit, with a "process" being one particular way of using
them.

This topic also covers:

- [Creating processes](~peios/threads-and-processes/creating-processes) — how a
  process starts another, and what the new one begins with.
- [Process lifecycle](~peios/threads-and-processes/process-lifecycle) — how a
  process ends, and how the system cleans up after it.
- [Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control)
  — the process tree, process groups, and sessions (distinct from the logon
  sessions in [Logon sessions](~peios/logon-sessions/overview)).

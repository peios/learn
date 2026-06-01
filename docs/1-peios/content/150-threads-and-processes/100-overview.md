---
title: Threads and processes
type: concept
description: A process is a program that is running; a thread is a single line of execution inside it. Everything the system does happens inside some thread, which makes processes and threads the actors the rest of Peios is built to reason about. This page introduces what they are; the topic goes on to cover how they are created, how they end, and how they relate.
related:
  - peios/identity/overview
  - peios/tokens/overview
  - peios/confinement/overview
---

A **process** is a program that is running. When you start a program, the system
loads it and gives it somewhere to run: a block of private working memory that
only it can see, a list of the files and other resources it currently has open,
and a name the system tracks it by. That running thing — the program plus
everything the system is keeping for it — is a process. When the program finishes
or you close it, its process goes away.

Most of the time a process does one thing at a time, step after step. But a
process can do several things at once by splitting into more than one **thread**.
A thread is a single line of execution — one sequence of steps the system is
working through. A process always has at least one thread (the instant it starts
running, that *is* its first thread), and it can start more. Every thread in a
process shares the same private memory and the same open resources, so they can
work together closely. What they don't share is their place in the sequence:
each thread runs its own steps, at its own pace, possibly all at the same time.

## The actors of the system

Processes and threads are the things that actually *do* work. Every action —
opening a file, sending data over a network, starting another program — is
carried out by some thread. When the system decides whether an action is allowed,
the question it answers is "is *this thread* allowed?" When it records that
something happened, it records which thread did it.

A thread always acts *as someone* — a person, a service, or the system itself.
Peios carries that "someone" along with the thread on a small object called a
**token** (see [Tokens](~peios/tokens/overview)). Two facts about it are worth
holding onto here:

- Every thread is always acting as someone. There is no "nobody" state.
- When one process starts another, the new process begins acting as the same
  someone as the process that started it.

## What a process has

The things the system keeps for every process:

| It has | Which means |
|---|---|
| Private memory | working space only this process can see; other processes can't read it |
| Open resources | the files, connections, and other things it currently holds open |
| An identity | who it is acting as (carried on its token) |
| A place in a family tree | every process was started by another, so processes form a tree |
| A lifecycle | it is created, it runs, and it ends — and something always notices when it ends |
| One or more threads | the actual lines of execution doing its work |

These are the main things, not the full list — a process also carries some other
things, like its **Process Security Block** (PSB), which holds its security-related
settings, that come up further on.

## Where to go next

Continue with [The process and thread model](~peios/threads-and-processes/the-process-and-thread-model)
to see how a thread and a process relate, and why a thread is really the more
basic idea, with a "process" being one particular way of using them.

This topic also covers:

- [Creating processes](~peios/threads-and-processes/creating-processes) — how a
  process starts another, and what the new one begins with.
- [Process lifecycle](~peios/threads-and-processes/process-lifecycle) — how a
  process ends, and how the system makes sure nothing is left dangling.
- [Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control)
  — the family tree, process groups, and sessions (which are a different thing
  from the logon sessions in [Logon sessions](~peios/logon-sessions/overview)).

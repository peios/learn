---
title: The process and thread model
type: concept
description: A thread is the basic unit of work — a single line of execution the system runs. A process is the boundary around one or more threads, holding the memory, open resources, and identity they share. This page explains how the two relate, and why a thread is the more fundamental of the two.
related:
  - peios/threads-and-processes/overview
  - peios/threads-and-processes/creating-processes
  - peios/tokens/overview
  - peios/impersonation/overview
---

A running program is made of two ingredients, and it helps to separate them.

The **thread** is the part that actually runs. A thread is one line of execution
— a single sequence of steps the system works through, one after another. The
steps are carried out by the **processor**, the part of the computer that does
the actual work; you'll often hear one called a **core**. Most computers have
several, so the system can genuinely run several threads at the very same instant,
one on each. A computer with only one can still run many threads by switching
between them so quickly that they all appear to move at once.
Deciding which thread runs, on which core, and for how long is the job of the
system's **scheduler** — a subject of its own. Either way, a thread
is the line of work being carried out — when you hear that "the system is doing
something", a thread is what's doing it.
Some tools and logs call a thread a **task** — it's the same thing: the part that
actually runs.

The **process** is the boundary around a group of threads. It doesn't run — it
*contains*. A process holds the things its threads share: their private memory,
their open files and connections, and their identity. Every thread inside one
process sees the same memory and the same open resources; threads in two
different processes do not. That separation is what stops one program from
reaching into another's memory or files by accident or on purpose.

So the relationship is: **the thread does the work; the process is the shared
space the work happens in.** A program that does one thing at a time is a process
with a single thread. A program that does several things at once is a process
with several threads, all sharing one space.

## Why the thread is the more basic idea

It is tempting to think of the process as the main thing and threads as something
extra it can grow. It is cleaner the other way around.

What the system fundamentally runs is threads. A "process" is just the answer to
the question *what does this thread share, and with whom?* Bundle some threads
together so they share one memory, one set of open resources, and one identity,
and you have called that bundle a process. Give a thread its own fresh, separate
memory instead of sharing an existing one, and you have made a new process for it.

This matters because it explains creation. Making a new thread and making a new
process are not two different mechanisms — they are the same act with a different
answer to "how much does the new line of execution share with the one that made
it?" Share everything, and the result is another thread in the same process.
Share nothing, and the result is a new process. Everything in between is possible
too. How that act is actually performed is covered in
[Creating processes](~peios/threads-and-processes/creating-processes).

## What threads share, and what they don't

Within one process, every thread shares:

| Shared across threads | What that means in practice |
|---|---|
| The process's memory | One thread can read and change data another thread is using — they cooperate closely, and must be careful not to trip over each other. |
| The open resources | A file one thread opens is usable by all of them. |
| The identity | By default every thread acts as the same someone (the process's identity). |

What each thread keeps to itself is its own **place in the sequence** — which step
it is on right now. That is the whole point of having more than one: each thread
makes progress through its own work independently of the others.

There is one exception to the shared identity. A single thread can temporarily
act as *someone else* — for example, a service handling a request can briefly act
as the person who made the request, do that one piece of work as them, and then
go back to normal. Only that one thread is affected, and only until it switches
back. This is covered in [Impersonation](~peios/impersonation/overview); here it
is enough to know that "every thread in a process shares the process's identity"
is the default, not an unbreakable rule.

## Naming a process

The system gives each process a number called its **process ID**, or **PID**, so
that people and other programs can refer to it — to check on it, send it a
message, or wait for it to finish. Threads are individually identifiable too, by a thread ID — see
[thread operations](~peios/threads-and-processes/thread-operations-reference).

A PID is short and convenient, but it only names a process while that process
exists. Once a process ends, its PID can later be reused for a completely
different process. So a PID tells you which process is which *right now*, but it
is useless as a lasting record — two unrelated processes can wear the same PID at
different times.

For that, every process also has a **Process GUID** (globally unique identifier):
a long name that is never reused, given to each process when it starts and fixed
for the rest of its life. Where the PID is the convenient short handle for the
moment, the Process GUID is the permanent one — it points at that one specific
process and no other, even long after it has ended. This is what lets a record of
something that happened on the system name exactly the right process, with no
chance of confusing two that happened to share a PID.

Both the PID and the GUID *refer* to a process. Neither says *who* the process is
acting as — that is a separate question, answered by its identity rather than by
any number or name.

## Where to go next

To see how a process or a thread is actually brought into being — and what a new
one starts out with — read [Creating processes](~peios/threads-and-processes/creating-processes).

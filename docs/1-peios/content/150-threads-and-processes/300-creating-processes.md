---
title: Creating processes
type: concept
description: New programs come to run through two basic moves — a process can split into a copy of itself, and a process can replace the program it is running with a different one. This page covers how processes are created, what a new one starts with, and how to get a reliable handle to it.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/threads-and-processes/process-lifecycle
  - peios/tokens/lifecycle
---

Every process on the system was started by another process. There is no way to
conjure one from nothing — a process that is already running has to make it. It
does so with two basic moves, which combine to cover every case.

## Splitting: one process becomes two

A running process can **split** into a copy of itself. The original keeps going,
and a second process appears beside it that begins as a near-identical copy. The
original is called the **parent** and the copy the **child**.

The child starts with:

- **Its own private memory**, copied from the parent. From the instant of the
  split the two memories are separate — a change one process makes is invisible
  to the other.
- **Copies of the parent's open resources** — the files and connections the
  parent had open, the child has open too.
- **The same identity** — the child begins acting as the same someone as its
  parent. (It inherits the parent's token; how the token carries across a split
  is in [Token lifecycle](~peios/tokens/lifecycle).)

It also gets things of its own that are *not* copied: a new PID, and a new Process
GUID — the child is its own distinct process, not a continuation of the parent.
A few pieces of per-process state start fresh rather than being inherited, too.

The move that does this is called **fork**.

## Replacing: same process, different program

A process can also **replace** the program it is running with a different one. It
keeps being the same process — same PID, same Process GUID, same identity — but
from that point on it is running entirely different code. Whatever it was doing
before is gone, replaced wholesale by the new program.

The move that does this is called **exec**.

## Putting them together

The two moves combine to launch a *different* program as a new process: a process
**splits**, and then the child immediately **replaces** itself with the program
you actually want to run. This split-then-replace pair is how most programs are
started — when you run a command, something forks and the child execs your
command. There is also a single combined step, **spawn**, that does both at once
for the common case.

Underneath, splitting is one setting of a more general move, **clone**, that lets
the creator choose *how much* the new line of execution shares with it. Share everything, and
the result is another thread in the same process; share almost nothing, and the
result is a new process — the two ends of the dial from
[the process and thread model](~peios/threads-and-processes/the-process-and-thread-model).
Everyday code rarely reaches for the general form directly; it makes threads or
spawns programs, which are the familiar settings of it.

The exact contract — every `clone` sharing flag, precisely what `fork` passes to a
child, and the variants of `exec` — is collected in the
[process creation reference](~peios/threads-and-processes/process-creation-reference).

## Getting hold of the new process

When a process creates a child, it usually wants to keep track of it — to wait
for it to finish, or to send it a signal later. For this it can hold a **handle**
to the child: a reference to that one specific process, called a **pidfd**. It is
the same kind of handle the system hands out for an open file — a small token your
program keeps and uses to refer back to the thing.

A process can be given a pidfd for its child at the moment it creates it, or ask
for one for a process that already exists. Either way the pidfd is tied to that
one specific process and can never be mistaken for another, so waiting on it or
signalling through it always reaches the intended target.

This is what makes a pidfd safer than a bare PID. A PID, recall, can be reused
once the process it named has ended; code that holds onto a bare PID risks later
acting on a completely different process that inherited the number. A pidfd never
has that problem — it refers to the one process it was made for and nothing else,
for as long as the program holds it.

## Where to go next

A process that has been created eventually ends. How it finishes, and how the
system makes sure nothing is left dangling, is in
[Process lifecycle](~peios/threads-and-processes/process-lifecycle).

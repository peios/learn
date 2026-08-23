---
title: Creating processes
type: concept
description: How processes are created — fork, exec, spawn, and clone — what a new process starts with, and how to hold a reliable handle to one with a pidfd.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/threads-and-processes/process-lifecycle
  - peios/security-fundamentals/tokens/lifecycle
---

Every process on the system was started by another process — a process that is
already running has to create it. Creation is built from two operations, which
combine to cover every case.

## Splitting: one process becomes two

A running process can **split** into a copy of itself. The original keeps
going, and a second process appears beside it that begins as a near-identical
copy. The original is called the **parent** and the copy the **child**.

The child starts with:

- **Its own private memory**, copied from the parent. From the moment of the
  split the two memories are separate — a change one process makes is
  invisible to the other.
- **Copies of the parent's open resources** — the files and connections the
  parent had open, the child has open too.
- **The same identity** — the child begins acting as the same principal as its
  parent. (It inherits the parent's token; how the token carries across a
  split is in [Token lifecycle](~peios/security-fundamentals/tokens/lifecycle).)

It also gets things of its own that are not copied: a new PID, and a new
Process GUID — the child is its own distinct process, not a continuation of
the parent. A few pieces of per-process state start fresh rather than being
inherited, too.

This operation is called **fork**.

## Replacing: same process, different program

A process can also **replace** the program it is running with a different one.
It remains the same process — same PID, same Process GUID, same identity — but
from that point on it runs entirely different code. Whatever the previous
program was doing is discarded, replaced wholesale by the new one.

This operation is called **exec**.

## Putting them together

The two operations combine to launch a different program as a new process: a
process **splits**, and the child immediately **replaces** itself with the
program to run. This split-then-replace pair is how most programs are started
— when you run a command, something forks and the child execs your command.
There is also a single combined step, **spawn**, that does both at once for
the common case.

Underneath, splitting is one setting of a more general operation, **clone**,
that lets the creator choose how much the new line of execution shares with
it. Share everything, and the result is another thread in the same process;
share almost nothing, and the result is a new process — the two ends of the
range from
[the process and thread model](~peios/threads-and-processes/the-process-and-thread-model).
Everyday code rarely uses the general form directly; it makes threads or
spawns programs, which are particular settings of it.

The exact contract — every `clone` sharing flag, precisely what `fork` passes to a
child, and the variants of `exec` — is collected in the
[process creation reference](~peios/threads-and-processes/process-creation-reference).

## Getting hold of the new process

When a process creates a child, it usually needs to keep track of it — to wait
for it to finish, or to send it a signal later. For this it can hold a
**handle** to the child: a reference to that one specific process, called a
**pidfd**. It is the same kind of handle the system hands out for an open
file.

A process can be given a pidfd for its child at the moment it creates it, or
ask for one for a process that already exists. Either way the pidfd is tied to
that one specific process and can never be mistaken for another, so waiting on
it or signalling through it always reaches the intended target.

This is what makes a pidfd safer than a bare PID. A PID can be reused once the
process it named has ended; code that holds a bare PID risks later acting on a
completely different process that inherited the number. A pidfd never has that
problem — it refers to the one process it was created for and nothing else,
for as long as the program holds it.

## Where to go next

A process that has been created eventually ends. How it finishes, and how the
system cleans up after it, is covered in
[Process lifecycle](~peios/threads-and-processes/process-lifecycle).

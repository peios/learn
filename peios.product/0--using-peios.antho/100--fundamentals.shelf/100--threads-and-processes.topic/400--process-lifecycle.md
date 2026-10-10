---
title: Process lifecycle
type: concept
description: Interpret process states, choose a safe way to end or pause a process, check the result, and understand zombies and orphaned children.
related:
  - peios/threads-and-processes/creating-processes
  - peios/threads-and-processes/relationships-and-job-control
  - peios/security-fundamentals/tokens/lifecycle
---

Read a process's state before deciding what to do. A sleeping process can be
healthy, a stopped process is paused rather than finished, and a zombie has
already ended. Use [Task Manager](~peios/threads-and-processes/task-manager) to
check the process, its parent, and whether a service or job manages it.

## The states it passes through

While it exists, a process is in one of a handful of **states**, and the system
moves it between them. Most of the time it is either **running** — executing,
or ready to run the moment a core is free — or **sleeping**, paused while it
waits for something to happen, such as data to arrive or a timer to fire. A
sleeping process uses no processor time until what it is waiting for is ready;
most processes spend most of their lives asleep.

A few states are worth knowing by name:

- **Stopped** — suspended (for example by job control when a job is paused at
  the terminal); it does nothing until told to resume.
- **Traced** — stopped under the control of a debugger that has attached to it, so
  the debugger can inspect and step it.
- **Uninterruptible sleep** — waiting on something the system will not interrupt,
  almost always a brief piece of disk or device I/O. A process here cannot be woken
  or even killed until the operation finishes; it normally lasts an instant, and a
  process stuck in it is a sign that hardware or a filesystem is stuck too.
- **Zombie** — finished, but still held as a result waiting to be collected (see
  below).

Once its result has been collected the process is gone, removed from the system
entirely.

## End, suspend, or resume a process

First check the scope. **Stop service** or `svctl stop NAME` asks peinit to stop
a service and its processes; **Stop job** or `svctl job stop ID` stops a
submitted job. Ending a service's main process directly can count as a crash
and trigger a restart. See
[Controlling services](~peios/services-and-jobs/controlling-services).

For one process, Task Manager's **End process** asks it to end, then offers
**End it now** after five seconds if it is still there. The immediate option
does not let the program finish its work. Task Manager holds the process so a
reused PID cannot redirect that action.

From a terminal, use [`kill`](~peios/system-and-processes/kill). Replace `4821`
in these examples with the PID you have just checked:

```
$ kill 4821                 # send TERM: ask the process to terminate
```

Give it time to finish, then refresh Task Manager and check the result. Only
if `TERM` has failed, and losing unfinished work is acceptable, consider:

```
$ kill -KILL 4821           # force termination without application cleanup
```

> [!WARNING]
> `KILL` gives a program no chance to save work or run its cleanup. Recheck
> the current process before acting on the PID again: an exited process's
> number can be reused. A process in uninterruptible sleep cannot finish
> terminating until the operation it is waiting on finishes.

To **pause** a process and later let it continue, use the documented stop and
continue signals:

```
$ kill -STOP 4821           # suspend
$ kill -CONT 4821           # resume
```

Suspension is not completion: the process does no work until resumed. Check
that pausing it will not interrupt work other programs or people depend on.
This targets one process, not a whole service or terminal pipeline.

`TERM` and `KILL` require permission to terminate the process; `STOP` and `CONT`
require permission to suspend or resume it. Protected processes also require
sufficient program trust. Being an administrator or sharing a terminal
session does not bypass protection. See
[Process permissions](~peios/threads-and-processes/the-process-security-block#when-an-action-is-refused).

A successful `kill` exit status means the signal was **sent**, not that the
process has finished. Exit status `1` means a signal could not be sent, for
example because the process no longer exists or you may not signal it. Check
the refreshed process or managed-service/job status before declaring it stopped.

## Two ways a process ends

A process ends in one of two ways.

Most often it ends **on its own**: it finishes its work and stops. A process
that ends this way leaves behind an **exit status** — a small record of how it
went, usually just "succeeded" or "failed" (and, on failure, a number giving a
rough reason). The act of a process ending itself is called **exit**.

The other way is that a process is **ended by a signal** from outside. Its
exit status records the terminating signal. This is different from the
**stopped** state above, which means suspended and able to resume.

Either way, a record of the process remains until its result is collected.

## Collecting the result

Whenever a child changes state — ends, is stopped, or resumes — the system
sends its **parent** a signal, `SIGCHLD`, prompting it to check. The parent
then reads the child's exit status. This is called **waiting** for the
process.

Between the moment a process ends and the moment its parent collects the
result, the finished process is a **zombie**: no longer running, but with the
system still holding its exit status so the parent can read it. Despite the
name, a zombie is harmless — it does no work and uses almost nothing; it is a
result waiting to be collected. The instant the parent collects it, the zombie
is gone for good.

If a parent never collects, zombies accumulate — finished processes whose
results no one read. That is a fault in the parent, not normal behaviour.
Inspect the parent and its service or job; a zombie has already finished,
so sending it another termination signal does not make the parent collect it.

A parent holding a [pidfd](~peios/threads-and-processes/creating-processes) for its
child can wait on it directly — the dependable way to be told the exact moment the
child ends.

The exact calls — every `wait` variant, and how an exit status is read — are in the
[developer process lifecycle reference](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference).

## When the parent ends first

A parent does not always outlive its children. If a parent ends while one of
its children is still running, that child becomes an **orphan**.

Orphans are adopted automatically, and keep running with a new parent. The
system's first process — PID 1, which on Peios is **peinit** — is the final
adopter when no nearer subreaper takes responsibility. When the adopted child
ends, its new parent collects the result.

PID 1 is the catch-all. A **subreaper** can instead adopt orphaned descendants
within its own subtree; service and container managers use this to retain
responsibility for the work they launched. For the programmatic contract, see
[Orphan adoption and subreapers](~peios/developing-for-peios/process-runtime-reference/process-lifecycle-reference#orphan-adoption-and-subreapers).

## What the system cleans up

When a process ends, the system reclaims what it was using. Its private memory is
freed and its open files and connections are closed.

It also **releases its identity**. A process acts as a principal, carried on
its token; when the process ends, its hold on that token is released. If other
processes were sharing the same identity — for example, siblings from the same
login — the identity lives on for them, and the system clears it away only once
nothing is using it any more. The details are in
[Token lifecycle](~peios/security-fundamentals/tokens/lifecycle).

The process's PID becomes available for the system to assign to a future
process. Its Process GUID is not reused — it remains a permanent marker of
that one process, so records of what it did still point unambiguously back to
it long after it is gone.

## Where to go next

Processes are arranged into a family tree and grouped together in ways that
matter for running them. That is
[Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control).

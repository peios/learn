---
title: Task Manager
type: how-to
description: See what is running on the machine from the desktop — every process, which service or job it belongs to, who it runs as, its CPU and memory, its protection and mitigations — and what you may not see of it, and why.
related:
  - peios/threads-and-processes/overview
  - peios/threads-and-processes/the-process-security-block
  - peios/services-and-jobs/overview
  - peios/inspecting/processes
---

**Task Manager** shows what is running on the machine now: every
**process**, which is a program that is running, with how much of the
processor and memory it is using, what it belongs to, and who it runs as.
What is defined to run, rather than what is running, is Services
Manager's.

Start it from the launcher: **Task Manager**.

It looks at the machine as you, so it shows exactly what you may see of
each process, and says what you may not, and why.

## The processes

Each process is listed with its name, its **PID** (the number the system
knows it by while it runs), who it runs as, and its share of the processor
(**CPU**) and the memory it holds. The CPU share is of the whole machine,
since the last look, and is filled in from the second look on. The bar at
the bottom gives the totals.

**Group by** chooses how they are arranged:

- **Service** puts each process under the service or job it belongs to,
  as peinit, the service manager, started it. A service's heading says
  its state; a **job**, which is a program someone asked peinit to run and
  watch, such as a person's desktop session, says who it runs as.
  **Not in a service** holds peinit itself.
- **Person** puts each under the person or service it runs as.
- **None** lists them all together.

**Name**, **PID**, **CPU** and **Memory**, at the top of the list, sort
by that. **Find** narrows the list to processes whose name, PID, person or
service contains what you type.

The kernel's own threads, which no person runs, are left out; tick
**Kernel threads** to show them.

The list is read again every two seconds. **Refresh**, or **F5**, reads
it at once.

## A process in full

Select a process to see it in full on the right: what it is doing, how
long it has run, its CPU, memory and threads, what started it (select it
to go to it), the command it was started with, the service or job it
belongs to and which part of it this is, who it runs as, the signed-in
session it is part of, and its integrity.

**Protection** says whether the process is protected: signed as part of
Peios, which closes it to every process not signed at its level, however
much authority that process has. **Mitigations** are the hardening the
process runs with, such as no memory being both writable and executable,
each with what it does. See
[The process security block](~peios/threads-and-processes/the-process-security-block).

## What you may see

What you may see of a process is its own permissions' to say:

- **Its name, CPU, memory and what it belongs to** are visible to everyone,
  by default.
- **Who it runs as, and the command it was started with**, are visible to
  the person it runs as and to Administrators. Anyone else sees the
  process without them, and a note above the list says how many processes
  that is.
- **A protected process**, such as peinit or authd, is closed to
  everyone, Administrators included: only processes signed at its level
  may look into it. It is still listed, with its protection, and a note
  above the list says how many there are. Where peinit can say which
  service a protected process is, it is listed under that service.

A job is listed to whoever may query it, which by default is who asked
for it and Administrators. A process in a job you may not query is listed
under **A job**, and says so.

## In a terminal

There is no `ps` yet. [`logonse psb --pid PID`](~peios/system-and-processes/logonse)
shows a process's protection and mitigations, `logonse list` the
signed-in sessions and their processes, and `svctl status NAME` a
service's main process.

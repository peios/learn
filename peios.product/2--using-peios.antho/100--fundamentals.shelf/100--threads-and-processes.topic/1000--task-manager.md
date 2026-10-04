---
title: Task Manager
type: how-to
description: See what is running on the machine from the desktop — every process, which service or job it belongs to, who it runs as, its CPU and memory, its protection and mitigations; the jobs; and who is signed in — end a process, stop its service or job, and see what you may not, and why.
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
each process, and says what you may not, and why. It offers to change
something only where you may.

**Processes**, **Jobs** and **Signed in**, in the bar, switch between its
three lists.

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

## Ending a process, or stopping its service or job

Below a process's details are what you may do to it:

- **End process** asks first, then asks the process to end. One that
  hasn't ended after five seconds is offered **End it now**, which ends
  it at once, without its finishing what it is doing. The process is
  held onto from the moment you ask, so another process given the same
  PID later can't be ended by mistake.
- **Stop service**, for a process that belongs to a service, asks peinit
  to stop the service, and everything it started. It stays stopped until
  it is started again. Ending a service's **main process** instead
  counts, to peinit, as the service crashing, and it may start it again;
  the window says so before you do.
- **Stop job**, for a process in a job, asks peinit to stop the job.

Each is there only where you may do it: End process where the process's
permissions let you end it, and Stop where peinit says you may stop that
service or job. Where you may not, the pane says why instead. A protected
process can't be ended by any program not signed at its level.

## Jobs

A **job** is a program someone asked peinit to run and watch, outside any
service: a person's desktop session is one. **Jobs** lists them: what
each is, its state, who it runs as, and how far it says it has got. A job
in full shows what it last said of itself, its progress, its program and
process, who it runs as and who asked for it, when it started and ended,
and how it ended. **Stop job** is there where you may stop it.

peinit lists a job only to those who may see it: by default, whoever
asked for it, and Administrators. The others are left out, and the
window says so. A job that has ended stays in the list for a minute.

## Who is signed in

**Signed in** lists each **session**, which is one sign-in: who, how
(at the machine, on the desktop, over SSH, or over the network), since
when, and how many of its processes you can see. A session in full lists
its processes, each of which leads to it, and its desktop session, if it
has one. Services sign in too, each in a session of its own; tick
**Services' sessions** to show them.

The full list is the kernel's, which only Administrators may read.
Anyone else sees the sessions their own processes are in, and the window
says so.

### Signing someone out

**Sign out**, in a session's details, ends the session: authd ends every
process running in it, asking each to end and, after a few seconds,
ending any that haven't. The window asks first, and says so when the
session is its own. What came of it is said afterwards, including any
process authd couldn't end, which keeps the session open.

You may sign out your own sessions, and anyone's the machine's
permissions allow, which as shipped is Administrators. Where you may not,
the window says why. A service's session ends when its service is
stopped, and the kernel's own sessions never end. See
[Ending a session](~peios/logon-sessions/lifecycle).

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

A process in a job you may not see is listed under **A job**, and says
so.

## In a terminal

There is no `ps` yet. [`logonse psb --pid PID`](~peios/system-and-processes/logonse)
shows a process's protection and mitigations, `logonse list` the
signed-in sessions and their processes, `svctl status NAME` a service's
main process, `svctl stop NAME` stops a service, `svctl job list` lists
the jobs and `svctl job stop ID` stops one, `logonse end ID` signs a
session out, and `kill PID` ends a process.

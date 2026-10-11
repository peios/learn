---
title: Threads and processes
type: concept
description: Find what is running, distinguish a process from its service or job, interpret its state and identity, and choose a safe way to stop it.
related:
  - peios/threads-and-processes/task-manager
  - peios/threads-and-processes/process-lifecycle
  - peios/services-and-jobs/overview
  - peios/identity/overview
  - peios/tokens/overview
  - peios/confinement/overview
---

To see what is running, open **Task Manager** from the launcher. Find a
process by name or PID, check its CPU and memory, and select it to see who it
runs as and which service or job it belongs to. Start with the
[Task Manager guide](~peios/threads-and-processes/task-manager) for the controls
and the limits on what you can see.

A **process** is a running program, together with its memory, open resources,
and the state the system keeps for it. A **thread** is one line of execution
inside that process. Every process starts with one thread and can create
more; its threads share memory and open resources while each makes progress
through its own work.

## The actors of the system

Every action, such as opening a file or sending data, is performed by a
thread. The system checks whether that thread is allowed and records which
thread acted. Each thread acts as a person, a service, or the system itself;
there is no "nobody" state. Its [token](~peios/tokens/overview) carries that
identity, and a new child process begins with its parent's identity.

The thing to stop depends on what you want to achieve:

| You want to stop | Use | Why |
|---|---|---|
| One running process | Task Manager's **End process**, or `kill PID` | Asks that process to end; unsaved work may be lost. |
| A managed service and its processes | **Stop service**, or `svctl stop NAME` | Ending only its main process can look like a crash and cause a restart. |
| A submitted job | **Stop job**, or `svctl job stop ID` | Asks peinit to stop the managed job. |

A service is a persistent definition; a process is one thing running now.
A submitted job is work someone asked peinit to run and watch. A terminal's
job-control group is another use of "job", described in
[Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control).

## What a process has

| A process has | What to look for |
|---|---|
| Private memory | Its working space, shared by its own threads and separate from other processes. |
| Open resources | Files, connections, and other resources it holds open. |
| An identity | Who it runs as; its token controls what it may reach. |
| A place in a family tree | Its parent, shown by a parent PID (PPID). |
| A lifecycle | Whether it is running, sleeping, stopped, or has finished. |
| One or more threads | The lines of execution doing its work. |

The **PID** identifies a process while it exists and can be reused afterwards.
The **Process GUID** identifies that one process permanently. Neither tells you
who it runs as. For a lasting event record, use the GUID; before acting on a
PID, check the current process again.

The [Process Security Block](~peios/threads-and-processes/the-process-security-block)
(PSB) holds the GUID, protection, hardening and the process's own permissions.
Being able to see a process does not mean you may stop or inspect all of it.

## Where to start

- [Task Manager](~peios/threads-and-processes/task-manager): find a process,
  investigate resource use, and choose a process, service, or job action.
- [Process lifecycle](~peios/threads-and-processes/process-lifecycle): interpret
  states and safely end, suspend, or resume a process.
- [The process and thread model](~peios/threads-and-processes/the-process-and-thread-model):
  understand threads, PIDs, GUIDs, and identity.
- [Creating processes](~peios/threads-and-processes/creating-processes): understand
  why starting a program adds a process, and why a process can change programs.
- [Process relationships and job control](~peios/threads-and-processes/relationships-and-job-control):
  understand parents, terminal process groups, and sessions.
- [The Process Security Block](~peios/threads-and-processes/the-process-security-block):
  understand protection and access refusals.

The syscall and threading-library contracts are in the developer
[Process runtime reference](~peios/developing-for-peios/process-runtime-reference/overview).

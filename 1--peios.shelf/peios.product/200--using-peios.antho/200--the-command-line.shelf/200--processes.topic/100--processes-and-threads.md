---
title: Processes and Threads
type: concept
description: Distinguish execution, process identity, and managed workloads before inspecting or stopping work.
---

A process groups a program's memory and resources. Its threads execute the
work, sharing that process's address space and normally its open-resource
table. Threads still have their own execution state, and a thread can
impersonate a different principal while handling a request.

Use [Task Manager](~peios/processes/task-manager) to inspect running
processes. Identify the command, owner, parent, and managing service or job;
those answer different questions.

## Identity across creation and program replacement

A PID identifies a process while it exists and can later be reused. The
Process GUID identifies that particular process across its lifetime and in
historical records. Neither identifies the principal acting through it.

A fork creates a child with a new PID and Process GUID. Private memory starts
from the parent's contents, while inherited descriptors can still refer to
the same open resources. The kernel's [token
lifecycle](~kernel/internals/kacs/tokens/token-lifecycle) defines identity
inheritance, including the distinction between primary and impersonation
tokens. Do not infer all inherited authority from a displayed account name.

Exec replaces the running program within a process. Its PID and Process GUID
remain, but the executable and its signature-derived protection can change.
A launcher commonly creates a child and then executes its program. Thread
creation shares more state instead of creating another independent process.
The exact creation flags and library contracts belong in runtime references.

A pidfd holds a particular process rather than whichever process later owns
a number. Programs should use that handle for stable targeting. From a shell,
recheck a PID's current command, owner, and workload before acting on an old
number.

## Workload relationships

| Relationship | What it identifies |
|---|---|
| Parent and child | Creation and responsibility for collecting exit results. |
| Service | A supervised definition whose processes can be restarted. |
| Submitted job | Work submitted to Peinit for management. |
| Process group | Processes targeted together by terminal job control. |
| Job-control session | Process groups and their possible controlling terminal. |
| Logon session | The authentication record referenced by identity tokens. |

A terminal pipeline and a submitted Peinit job are different uses of "job."
A job-control session need not have a terminal and is not a security identity.
With ordinary terminal settings, Ctrl-C and Ctrl-Z signal its foreground
process group; an explicit signal to one PID has a narrower target.

Userspace ancestry normally leads to Peinit, PID 1. Orphaned descendants can
be adopted by a nearer subreaper before PID 1 takes responsibility. Kernel
threads and idle tasks are separate system work; a process listing is not
only a list of applications started by people.

## Identity and program protection

The effective token describes who a thread acts as. The Process Security
Block describes the process: its GUID, program protection, mitigations, and
process security descriptor. Impersonation changes the effective identity,
not the calling program's protection.

Reading a limited process summary does not grant permission to inspect its
memory or stop it. A process's descriptor and Process Integrity Protection
can refuse those operations even when its row remains visible. See
[Inspecting Process Security](~peios/identity-and-access/inspecting-process-security).
For managed work, ask the manager to perform the intended operation through
its own policy rather than repeatedly terminating a supervised PID.

---
title: The Process Security Block
type: concept
description: The Process Security Block (PSB) records what a process is — its program's trust, its hardening, and who may operate on it — as distinct from who it acts as.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/process-integrity-protection/overview
  - peios/process-mitigations/overview
---

When Task Manager hides details or refuses **End process**, inspect the
process's **Protection** and **Mitigations**. In a terminal,
[`logonse psb --pid PID`](~peios/system-and-processes/logonse) shows its protection,
hardening and Process GUID without changing them.

A process's identity — who it is acting as — is carried on its token, and can
change moment to moment, since a thread can impersonate another principal. A
process has a second aspect that is independent of identity: **what it is**.
What program is it running? How trusted is that program? How hardened is it
against attack? Who is allowed to operate on it?

Those facts are gathered in one place — the **Process Security Block**, or **PSB**.
Every process has one. Where the token answers who this process is acting as, the
PSB answers what this process is. Unlike the token, the PSB never changes when a
thread impersonates: impersonation changes who, never what.

## What the PSB holds

- **Its permanent name.** The process's
  [Process GUID](~peios/threads-and-processes/the-process-and-thread-model) — the
  never-reused identifier — lives on the PSB.
- **How trusted its program is.** When a process starts running its program, the
  system checks the program's cryptographic signature and records from it how
  trusted the program is. This is the process's **PIP** (Process Integrity
  Protection) label, and it decides which other processes are allowed to
  inspect, signal, or interfere with this one. The barrier is based on what
  program is running, not on who is running it: even a fully privileged process
  cannot disturb a more-trusted one. The full treatment is
  [Process integrity protection](~peios/process-integrity-protection/overview).
- **How it is hardened.** A set of **mitigations** — restrictions the process
  carries on what it may do with its own memory and code, so that a bug or
  injected code has far less room to do harm. They can only ever be tightened,
  never loosened. The catalog and rules are
  [Process mitigations](~peios/process-mitigations/overview).
- **Who may operate on it.** Every process has its own security descriptor — the
  rules for who is allowed to act on the process itself: inspect it, signal it, and
  so on. It lives on the PSB alongside the rest.

A few more specialised settings live here too — a process can be marked so that it
may no longer create children, for instance — but those four are the core.

## Inspecting and managing the PSB

A process's PSB can be read by anyone the process's permissions let see its
name and CPU use, which by default is everyone — even where the process is
protected and nothing else about it can be seen. That is what lets a tool say
*why* a process is closed to you.

- On a terminal, [`logonse psb --pid PID`](~peios/system-and-processes/logonse)
  shows a process's protection, mitigations and GUID, and with `--mitigations`
  turns mitigations on.
- On the desktop, [Task Manager](~peios/threads-and-processes/task-manager)
  shows them for the process you pick.
- From a program, read `/proc/<pid>/psb`, or call `peios_process_psb` in the
  SDK.

## When an action is refused

Being able to see a process's name or PSB does not grant control of it. Its
security descriptor determines which actions your identity may perform.
Signals also have to pass **Process Integrity Protection** (PIP): the program
sending the signal must have enough trust to act on the target.

| Action | Process right |
|---|---|
| Read the PSB | `PROCESS_QUERY_LIMITED` |
| Read detailed process information | `PROCESS_QUERY_INFORMATION` |
| Send terminating signals, including `TERM` and `KILL` | `PROCESS_TERMINATE` |
| Suspend or resume with `STOP` or `CONT` | `PROCESS_SUSPEND_RESUME` |

The PSB inspection surface does not require PIP dominance, which is why a
tool can explain that a process is protected even when its other details are
closed. Detailed inspection and signalling still require it. Even
`SeDebugPrivilege` does not bypass PIP, and impersonating a different identity
does not change the calling program's trust.

For a managed service, use **Stop service** or `svctl stop NAME` when permitted.
That asks peinit to perform the managed action under the service's own
permissions, instead of trying to signal its protected process directly.
See [Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service).

## Before changing mitigations

`logonse psb --pid PID` is an inspection command. Adding `--mitigations MASK`
changes hardening: those flags can only be turned on, never cleared during the
process's lifetime. Check the [mitigation rules](~peios/process-mitigations/overview)
and the [`logonse` reference](~peios/system-and-processes/logonse) before using
that option. It is not a way to gain permission to inspect or end the process.

## Where to go next

The two largest parts of the PSB each have a topic of their own:
[Process integrity protection](~peios/process-integrity-protection/overview), for the
trust label that governs which processes may interfere with which, and
[Process mitigations](~peios/process-mitigations/overview), for the self-hardening
flags and how they are applied.

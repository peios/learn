---
title: The Process Security Block
type: concept
description: The Process Security Block (PSB) records what a process is — its program's trust, its hardening, and who may operate on it — as distinct from who it acts as.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/process-integrity-protection/overview
  - peios/process-mitigations/overview
---

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

Because the PSB is where a process's trust level and hardening live, there is a
dedicated tool for working with it: the **`psb`** command, which inspects a
process's PSB and manages its mitigations and PIP mode.

## Where to go next

The two largest parts of the PSB each have a topic of their own:
[Process integrity protection](~peios/process-integrity-protection/overview), for the
trust label that governs which processes may interfere with which, and
[Process mitigations](~peios/process-mitigations/overview), for the self-hardening
flags and how they are applied.

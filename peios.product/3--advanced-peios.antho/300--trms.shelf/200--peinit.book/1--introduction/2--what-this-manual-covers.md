---
title: What This Manual Covers
description: The scope of this manual, what in peinit is a contract and what is not, and where the constants and registry keys live.
---

This manual describes peinit as it is built: the boot sequence, the
service model and its registry schema, how a service acquires its
identity, the exact sequence between "start this" and "the binary is
running", the state machine and its causes, dependencies, jobs and
operations, timers, output handling, shutdown, and the security model.

## What is a contract and what is not

Two of peinit's interfaces are specified separately, in PSPU §4: the
**control socket**, spoken by administrative tools and by any program
that manages services, and the **notification socket**, spoken by every
service that reports readiness, keepalives, or a stored descriptor.
Those are contracts. A third party implements one side of each, and what
is written there binds both.

This manual covers the other side of that boundary — how peinit fulfils
them, and everything that is not a contract at all:

- how a command becomes an operation, and what happens when two of them
  collide (§8.2, §8.3)
- what a command does to a service in each state (§10.3)
- how a notification is authenticated and applied (§10.5, §10.6)

Where a chapter touches the contract it references PSPU §4 rather than
restating it.

The **service definition schema** is here rather than in PSPU. It is
registry configuration, protected by the registry's descriptors and
administered by the same tools as the rest of the registry, and it is
documented for the people who write service definitions rather than
specified as a wire format. §3.2 is the reference.

## What this manual does not cover

- **KACS** — tokens, Security Descriptors, AccessCheck, and the
  per-service SID algorithm peinit reproduces. Peios Kernel TRM §3.
- **LCS** — the registry syscalls, watches, and layer resolution peinit
  reads through. Peios Kernel TRM §5.
- **KMES** — the ring buffer peinit emits its events into. Peios Kernel
  TRM §2.
- **loregd** — the storage behind registryd. Its own TRM.
- **eventd** — where the logs and events go. Its own manual.
- **authd** — token minting and identity routing. peinit's requirements
  of it are described in §4.3; its interface is authd's own.
- **JFS** — the kernel side of ad-hoc job submission. §8.5 describes
  what peinit does with what JFS hands it.
- **Using peinit** — writing service definitions, the `svctl` command
  surface, and everyday administration are covered in Using Peios.

## Constants and keys

Registry keys and compiled-in constants are collected in the appendices,
so a chapter's reference material does not interrupt the prose that
explains it. Where an appendix defines a value the body references it
rather than repeating it.

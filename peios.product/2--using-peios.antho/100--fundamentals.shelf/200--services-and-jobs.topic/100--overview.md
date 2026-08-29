---
title: peinit
type: concept
description: peinit is PID 1 — the single service manager. Services, jobs, and operations; identity built in; and how it differs from the init systems you know.
related:
  - peios/services-and-jobs/defining-a-service
  - peios/services-and-jobs/the-service-lifecycle
  - peios/services-and-jobs/controlling-services
  - peios/services-and-jobs/boot-and-boot-modes
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/tokens/overview
  - peios/registry-concepts/overview
---

**peinit** is the init system of Peios — the first userspace process, running at PID 1 for the lifetime of the machine. It is a single-threaded program with one job: manage services, from the first one started at boot to the last one stopped at shutdown. Every supervised process on a Peios system — a long-running daemon, a one-shot setup task, a health check, a scheduled job — is started, watched, and reaped by peinit.

What makes peinit its own thing is that **identity is built in**. peinit does not just launch processes; it launches them *as someone*. Each service runs under a [KACS token](~peios/tokens/overview) that decides what it can reach, and each service is itself a securable object with a [security descriptor](~peios/security-descriptors/overview) that decides who may start, stop, or query it. Service management and access control are the same system, not two systems bolted together.

This page sketches what peinit is responsible for, names the handful of ideas that make it unlike other init systems, and points at the pages that cover each one.

## peinit in one sentence

**peinit is the sole service manager and PID 1 — it reads service definitions from the registry, starts them in dependency order under per-service identities, supervises them through a defined state machine, and tears them down in reverse at shutdown.**

Everything in this topic is an elaboration of that sentence: what a *service definition* is, what *dependency order* means, what the *state machine* looks like, how *identity* is materialised, and how you drive the whole thing from a shell.

## Three kinds of object

peinit is easiest to understand through the three first-class objects it works with. Keeping them straight is most of the battle when you read a status output or an event log.

| Object | What it is | Lifetime |
|---|---|---|
| **Service** | A *definition* — a named unit of execution with identity, policy, and configuration, stored in the registry. It has a runtime state (the [state machine](~peios/services-and-jobs/the-service-lifecycle)) and, when running, a process. | Long-lived. Persists across restarts and reboots. |
| **Job** | A single *process execution*. Every time peinit forks — a service's main process, a hook, a health check, a submitted job — that is one job, with its own GUID and exit result. | Short-lived. A restart creates a *new* job. |
| **Operation** | A *requested action* on a service — start, stop, restart, reload, reset. Control commands create operations that are validated, queued, and executed. | Short-lived. Resolves to a terminal state, then is dropped. |

A service is the *what*; a job is *what actually ran*; an operation is *what someone asked for*. A single `restart` command, for example, is one **operation**, which stops the current **job** and starts a new one, all against one **service**. Jobs and operations both carry GUIDs and are emitted to [eventd](~peios/auditing/overview) as they complete, which is how the history of a service is reconstructed after the fact. They get their own page: [Jobs and operations](~peios/services-and-jobs/jobs-and-operations).

Underneath all three sits the fourth thing peinit is always handling — the **token**, the identity a service runs under. Tokens are not peinit's invention; they are the [system-wide identity object](~peios/tokens/overview). peinit's role is to obtain the right token for each service and install it before the process runs. That is the subject of [Service identity and privileges](~peios/services-and-jobs/identity-and-privileges).

## What peinit is not

peinit borrows vocabulary from init systems you may already know, and the familiarity is a trap. Clearing three wrong mental models is most of understanding what peinit actually is.

**It is not systemd.** There are no unit files. peinit does not read, parse, or translate `.service` files, and there is no migration shim. A service definition is a key in the [registry](~peios/registry-concepts/overview) under `Machine\System\Services\`, made of typed registry values — not a text file under `/etc`. Some *interfaces* are deliberately compatible where that helps: peinit speaks the `sd_notify` readiness protocol, and timer schedules use systemd's `OnCalendar` calendar-expression format. The compatibility stops at those wire formats; the model underneath is different.

**It is not Windows SCM.** The influence is real — services as securable objects with per-service descriptors, token-based service identity, an access-controlled control interface, a structured state machine — but it is *architectural*, not interface-level. peinit does not implement the SCM RPC protocol, Windows service types, or Windows control codes.

**It is not a logging system.** peinit holds a service's `stdout`/`stderr` pipes at birth, so it controls *where* output goes — but storage, indexing, and queries are [eventd](~peios/auditing/overview)'s job. peinit forwards; eventd is the historian. The same split applies to job and operation history: peinit emits structured events and forgets them; eventd keeps them. See [Service output and logging](~peios/services-and-jobs/output-and-logging).

A fourth, smaller correction: **peinit does not supervise forking daemons.** A service that double-forks to "daemonise" is solving a problem that does not exist when the manager tracks the process it spawned. peinit tracks every process by [pidfd](~peios/services-and-jobs/service-types); a legacy binary that insists on double-forking must be wrapped at the package layer.

## The one operational invariant

peinit is **single-threaded PID 1**, and that one fact explains a surprising amount of its design. In a single-threaded PID 1, a blocking system call blocks *everything* — child reaping, watchdog expiry, shutdown signals, every other event stops while the call is stuck. So peinit's hard rule is that **its event loop never blocks on a userspace service.**

Two consequences you will meet repeatedly:

- **peinit operates on an in-memory snapshot of the registry, not a live view.** It reads all service definitions synchronously *once*, during boot, and thereafter works from an in-memory model that it updates from [change notifications](~peios/registry-concepts/watches). Supervision never waits on the registry being available. This is why a configuration change does not always take effect immediately — see [Defining a service](~peios/services-and-jobs/defining-a-service).
- **Anything that could block is pushed off the main loop.** Filesystem condition checks run in a short-lived forked helper rather than a `stat()` on the event loop; token requests to authd are driven by a timed state machine, not a blocking call; log delivery is best-effort and never exerts back-pressure on peinit.

You do not need to think about the event loop to operate peinit, but it is the reason behind several behaviours that would otherwise look arbitrary.

## Where peinit sits in the system

peinit is part of the [Trusted Computing Base](~peios/boot-and-trust-establishment/overview): a compromise of peinit is a compromise of the whole machine. It runs as [SYSTEM](~peios/identity/well-known-principals) with all privileges, and it never drops that identity. It depends on, and is depended on by, the other TCB components:

| peinit relies on | For |
|---|---|
| **KACS** | Service identity (installing tokens on children), control-interface authentication (peer token + AccessCheck), and per-service access control. See [Access decisions](~peios/access-decisions/overview). |
| **LCS / the registry** | Service definitions, boot configuration, and its own parameters. See [The registry](~peios/registry-concepts/overview). |
| **registryd** | The registry *source* daemon — the first service peinit starts. peinit treats it as an opaque dependency. (`registryd` is an interface; the default implementation is `loregd` — see [Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes).) |
| **authd** | Minting tokens for non-platform services. peinit requests; authd mints. |
| **eventd** | Service logs (forwarded over a socket) and job/operation/audit events (emitted through KMES). |
| **KACS, again** | Conveying a job identity: when a process submits a job over peinit's jobs socket and attaches a token, the kernel gates the attach — so peinit can run a program as a service's client without ever judging the identity itself. See [Jobs and operations](~peios/services-and-jobs/jobs-and-operations). |

The bootstrapping puzzle — authd needs the registry, the registry needs to be started by *something*, and that something is peinit running before any of them exist — is resolved by the boot model in [Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes).

## Where to start

If you are configuring a system, start with **[Defining a service](~peios/services-and-jobs/defining-a-service)** — what a service definition is, where it lives, and the rule that explains why some changes take effect immediately and others wait for a restart.

If you want to *operate* a running system — start, stop, query, and troubleshoot services — go to **[Controlling services](~peios/services-and-jobs/controlling-services)** for the command set and **[The service lifecycle](~peios/services-and-jobs/the-service-lifecycle)** to read what a status actually tells you.

If you care about *what runs as whom*, read **[Service identity and privileges](~peios/services-and-jobs/identity-and-privileges)** and **[Who can manage a service](~peios/services-and-jobs/who-can-manage-a-service)** — the two independent halves of the security model.

If you are investigating boot behaviour, **[Boot and boot modes](~peios/services-and-jobs/boot-and-boot-modes)** covers Full, Safe, and Recovery modes and the escalation between them.

And when something is wrong, **[Troubleshooting peinit](~peios/services-and-jobs/troubleshooting)** works backward from the symptom.

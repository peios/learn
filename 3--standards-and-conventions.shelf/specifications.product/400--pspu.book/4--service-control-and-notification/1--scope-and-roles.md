---
title: Scope and Roles
description: The two interfaces a Peios service manager offers — the control channel and the notification channel — and what this chapter leaves out.
---

This chapter defines the two interfaces a Peios service manager offers:
the **control channel**, by which a program manages services, and the
**notification channel**, by which a supervised service reports on
itself.

Both are Unix-domain sockets between userspace parties, and both have a
publicly implementable side. A monitoring tool, an orchestration agent,
a shell utility, or a privileged action broker implements the client
side of the control channel. Every supervised service that reports
readiness, sends keepalives, or preserves file descriptors across a
restart implements the producer side of the notification channel.

## The roles

**The manager** is the process that supervises services. It listens on
both channels. On Peios this is peinit, running as PID 1, but nothing
here depends on that beyond the manager being a single process holding
both sockets.

**A client** connects to the control channel to issue commands and read
answers. A client is any process; it holds no special relationship with
the manager beyond the one its token establishes.

**A service** is a process the manager started, and speaks the
notification channel about itself. A service does not connect to the
control channel in that capacity — a program that does both is acting in
two roles.

**A job** the manager started on a submitter's behalf (§7) speaks the
notification channel exactly as a service does, and is observed and
stopped from the control channel by the job commands of §4.14. The
channel by which it is submitted is §7's.

Requirements are stated against the role, not the program.

## What this chapter covers

- the two channels, their addressing, and how each is reached
- message framing and encoding on both
- how a client's identity is established, and how a command is
  authorised
- the command set, the response shapes, and the error vocabulary
- what a command does to a service in each of its states
- how a service's notification is authenticated, and what a service may
  say
- the file-descriptor store
- the rules under which either channel may be extended
- the conformance requirements for each role

## What this chapter does not cover

- **How the manager supervises anything.** Dependency resolution,
  restart policy, timers, cgroups, the boot sequence and shutdown are
  the manager's own design. This chapter defines what a client can ask
  for and what it is told, not how the answer comes about.
- **How service definitions are expressed.** On Peios they are registry
  keys, administered like any other registry data. That is the service
  manager's own design.
- **What a service state means.** The vocabulary is fixed here
  (§4.B) because it appears on the wire; what causes a service to be in
  one of those states is not.
- **Kernel interfaces.** Establishing a peer's identity and evaluating
  an access decision are kernel operations, specified in PSPK and in
  the kernel's own reference manual.
- **Submitting a job.** The channel by which a process asks the manager
  to run a program under supervision, the identity such a job runs as,
  and the commands its submitter issues about it are §7. This chapter
  covers only what a control-channel client sees of such a job.

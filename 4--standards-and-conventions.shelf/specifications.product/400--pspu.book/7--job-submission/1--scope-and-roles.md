---
title: Scope and Roles
description: The interface by which any process asks the service manager to run and supervise a process on its behalf — the submitter's side of a job, and what this chapter leaves to §4.
---

This chapter defines the **jobs channel**: the interface by which a
process asks a Peios service manager to run an arbitrary program under
its supervision, with an identity the requester is entitled to confer,
and to manage that program afterwards.

A job submitted this way is a **job** in the sense of §4.2 — one
process execution, supervised by the manager — whose parent is the
process that asked for it rather than a service definition. The
manager forks it, installs its token, contains it, records it and
reaps it exactly as it does a service's process. What differs is where
the definition came from and who is entitled to manage the result.

Two shapes of use are intended, and the chapter is written so that one
primitive serves both:

- A **task**: a program that runs to completion and reports progress
  on the way — a backup, a transfer, a migration — submitted by a
  broker on behalf of the principal it is acting for.
- A **session**: a long-lived program managed from outside — a
  per-logon host process for an interactive session — submitted with a
  freshly issued logon token and one end of a channel back to its
  submitter.

Nothing in the protocol distinguishes the two. They are the same
message with different field values.

## The roles

**The manager** is the process that supervises services and listens on
the control and notification channels of §4. It listens on the jobs
channel too. On Peios this is peinit.

**A submitter** connects to the jobs channel, submits a job, and MAY
manage the jobs it submitted. A submitter is any process the socket's
descriptor admits; it holds no relationship with the manager beyond
the one its token establishes.

**A job** is the process the manager started on a submitter's behalf.
It speaks the notification channel of §4 about itself, in the same way
a service does, and this chapter adds nothing to that role beyond the
progress fields defined in §4.19.

**A client** of the control channel (§4) MAY observe and stop jobs it
is entitled to, alongside services. That role is unchanged here;
§4.14 defines the commands.

Requirements are stated against the role, not the program. A service
that submits jobs is a submitter when it does so; a job that submits
jobs of its own is a submitter too.

## What this chapter covers

- the jobs socket, how it is reached, and who may reach it
- message framing on it, and how a message carries a token and
  descriptors alongside its content
- how the identity a job runs as is established, and the rule that
  the manager never installs an identity the submitter could not
  already act as
- the job definition a submitter sends, and what the manager validates
- the job view the manager reports, its states and its causes
- the commands a submitter may issue about its own jobs, and the
  Security Descriptor that decides who else may
- passing descriptors into a job, and receiving its output
- the error vocabulary, the extension rules and the conformance
  requirements

## What this chapter does not cover

- **The notification channel**, including the progress fields a job
  sends. A job reports on itself exactly as a service does. §4.16–§4.19.
- **Observing and stopping jobs from the control channel.** The
  `job-list`, `job-status` and `job-stop` commands are part of the
  control channel's command set and are defined in §4.14, using the
  job view this chapter defines.
- **How the manager supervises the job** once it is running — cgroup
  containment, output capture, reaping, the child setup sequence. That
  is the manager's own design, documented in its reference manual.
- **How a token is conveyed on a socket, and what the kernel checks
  when it is.** Peer-token capture, `KACS_SCM_TOKEN`, the impersonation
  gates and the impersonation-level ratchet are kernel operations,
  documented in the Peios Kernel TRM §3.5.
- **How a submitter obtained the token it attaches.** From a peer it is
  serving, from a logon it originated (PGSS §2), or from anywhere else
  — the manager does not ask, because the kernel has already decided
  whether the submitter may convey it.

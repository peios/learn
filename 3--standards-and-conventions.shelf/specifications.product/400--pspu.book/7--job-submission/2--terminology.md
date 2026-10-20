---
title: Terminology
description: Terms this chapter defines for itself — submitter, submitted job, job identity, attached token, message — and the ones it borrows from §4 and the kernel manual.
---

Terms defined in §4.2 — service, job, activation generation, right,
terminal state, datagram — are used here with the same meaning and are
not redefined.

**Submitted job.** A job whose definition arrived on the jobs channel
rather than from a service definition. It has no service, no
operation, and no activation generation; it belongs to a submitter.

**Submitter.** The principal that submitted a job: the identity the
connection carried when the `submit` message was read. It is recorded
on the job and is the owner of the job's Security Descriptor.

**Job identity.** The identity a submitted job's process runs as. It
is either the submitter's own primary identity or one the submitter
attached to the `submit` message; it is never named by a field.

**Attached token.** A token conveyed with a message through the
kernel's per-message identity facility (`KACS_SCM_TOKEN`; the Peios
Kernel TRM §3.5). The kernel has verified, at the moment of sending,
that the sender could act as that identity at the level recorded on
the token.

**Attached descriptor.** A file descriptor conveyed with a message
through `SCM_RIGHTS`, to be given to the job or used as its output
sink.

**Message.** One `SOCK_SEQPACKET` record on the jobs channel, carrying
exactly one JSON object and, optionally, one attached token and any
number of attached descriptors. The jobs channel has no frames in the
sense of §4.2: the transport delimits messages.

**Job view.** The JSON object by which the manager reports a job, on
either channel. §7.7.

**Live job.** A submitted job in a non-terminal state. Quotas count
live jobs.

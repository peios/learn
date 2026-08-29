---
title: Sender Authentication
description: A datagram claims to be a service talking about itself; the steps by which a manager establishes that it is, and what it must never use.
---

A datagram on this channel claims to be a supervised process — a
service, or a submitted job (§7) — talking about itself. The manager
MUST establish that it is.

## The requirements

The manager MUST enable `SO_PASSCRED` on the socket, and MUST reject any
datagram arriving without a kernel-attested credentials control message.

It MUST then establish all of the following, and MUST drop the datagram
if any fails:

1. **The sender is a service's current main job, or a submitted job.**
   The manager MUST match the attested PID against the main jobs and
   the submitted jobs it is supervising. A hook process, a health check,
   or a child a service or a job forked MUST NOT be able to notify on
   its behalf.
2. **That job has exec'd and is running.** A job still in setup has not
   become the service yet.
3. **That job has a kernel handle on the process** — a pidfd, or an
   equivalent that refers to one specific process rather than to a
   number.
4. **The handle still refers to the attested PID.** The manager MUST
   verify the PID against the handle rather than trusting the PID alone.
5. **For a service's job, its activation generation is the service's
   current one.** A submitted job has no generation and no replacement;
   the step does not apply to it.

## Why steps 3 and 4 exist

A PID identifies a process only until that process exits. Between a
service writing a datagram and the manager reading it, the service can
die and its PID be recycled onto something else — and PID matching alone
would then attribute the unrelated process's message to the service, or
attribute the service's message to whatever now holds the number.

A handle obtained atomically at fork does not have that property.
Verifying the attested PID against the handle is what turns a probable
match into a certain one.

## Why step 5 exists

A datagram sent by an incarnation of a service that has since been
restarted MUST NOT be applied to its replacement. Without the generation
check, a `READY=1` written by a process moments before it crashed could
mark the process that replaced it ready — declaring a service healthy on
the strength of a message from the one that just failed.

Readiness is per activation generation, and so is everything else on
this channel.

## What the manager MUST NOT use

The manager MUST NOT use the sender's UID or GID as an authorisation
input, and MUST NOT accept any identity a service asserts in the
datagram's content.

Identity on this channel is *which supervised process this is*, and only
the kernel can attest that. A service does not have a name here that it
gets to state, and a job does not have an identifier.

## What a job may send

A submitted job may send every field in §4.19. Those that address a
service transition it is not in — `RELOADING`, `EXTEND_TIMEOUT_USEC`
outside a readiness wait, the descriptor-store fields, which a job has
no store for — MUST be applied as §4.19 says for the case where they do
not apply: ignored, or closed and recorded. `READY=1` from a
`readiness: none` job is ignored. A job's `STATUS` and `PROGRESS` are
retained and exposed in its job view (§7.7).

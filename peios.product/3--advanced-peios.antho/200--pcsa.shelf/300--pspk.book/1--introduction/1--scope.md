---
title: Scope
description: What PSPK is — the protocols spoken across the kernel boundary between a kernel subsystem and the userspace process serving it — and how trust runs across that line.
---

This document defines the **Peios System Protocols Kernel (PSPK)**: the
protocols spoken across the kernel boundary, between a kernel subsystem
and a userspace process that serves it.

A contract belongs in this document when both of these hold:

- one party is a kernel subsystem and the other is a userspace process;
  and
- the userspace side is a public, implementable role — a third party can
  write a program that fills it.

The two parties need not be in conversation. A live protocol has a
kernel subsystem and a process exchanging messages; a **format** has one
side producing an artifact that the other consumes, perhaps long
afterwards and on a different machine. Both are specified here, because
both are contracts a third party has to satisfy exactly.

The second condition is what separates a PSPK protocol from a system-call
surface. A system call is an interface the kernel offers to any program
that asks. A PSPK protocol is a contract the kernel depends on some
program to fulfil: the kernel is the party asking, and the userspace
process is authoritative for the answer.

For each protocol, this document covers:

- the channel, and how a userspace party attaches to it and is
  recognised
- message or artifact framing, encoding, and the rules under which the
  format may be extended
- the requests the kernel issues, the responses it expects, and their
  ordering
- what the kernel-side party validates for itself rather than believing
  from a response
- behaviour on failure, refusal, and disconnection
- the conformance requirements for the userspace role

This document does not cover:

- The behaviour and data model of the kernel subsystem itself — defined
  in that subsystem's specification
- System-call and ioctl surfaces — defined in that subsystem's
  specification
- The binary structures these protocols carry — defined in PCDS
- Standards a system MUST implement to be Peios — defined in PGSS
- Protocols between userspace components — defined in PSPU
- How a userspace implementation stores its data or computes its
  answers — its own design

## Trust across the boundary

A PSPK protocol crosses a trust boundary in the direction that matters
most: a kernel subsystem is asking a lower-privileged process for
something it will then act on. Every specification in this document
therefore states explicitly which parts of a response the kernel
establishes for itself and which it takes on the userspace party's word.

## Relationship to PGSS

A protocol in this document is not a conformance requirement in the sense
PGSS defines. It is the interface a particular Peios kernel subsystem
uses to reach the processes that serve it; a system built from different
kernel subsystems is still Peios. These protocols are specified because
they are public even so — a third party writing an implementation of the
userspace role needs the contract written down.

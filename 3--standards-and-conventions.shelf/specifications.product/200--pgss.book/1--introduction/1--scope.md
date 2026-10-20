---
title: Scope
description: What PGSS is — the cross-platform standards a system must implement to be Peios — and the test that separates a standard from a protocol.
---

This document defines the **Peios Generic System Standards (PGSS)**: the
cross-platform protocols and standards a system MUST implement in order
to be Peios.

A standard belongs in this document when three things are true of it.

**It is a conformance requirement.** A system that does not offer the
protocol, at the specified path, with the specified semantics, is not
Peios. Each standard here is a bar to clear, not a recommendation to
weigh.

**It belongs to no implementation.** A PGSS standard describes a contract
between two roles, not the behaviour of a particular program. Mainline
ships an implementation of each role; nothing in this document depends on
that implementation, or describes it.

**Either role may be replaced.** A third party MAY ship its own
implementation of one role — or of both — and interoperate with the other
unchanged. A standard that cannot survive that substitution is a
description of one system rather than a contract between two, and does
not belong here.

For each standard, this document covers:

- the channel it is offered on, and the access control governing it
- message framing, encoding, and the rules under which the format may be
  extended
- the messages exchanged, their fields, and the order in which they are
  exchanged
- the obligations binding on each role, including what a role MUST
  establish for itself rather than believe from a message
- the conformance requirements for each role

This document does not cover:

- How an implementation reaches the answers it gives — that is precisely
  what different systems exist to do differently
- The binary structures these protocols carry — defined in PCDS
- Protocols spoken across the kernel boundary — defined in PSPK
- Protocols between foundational userspace components — defined in PSPU
- Interfaces particular to one Mainline component — defined in the
  specification of the component that offers them

## Distinguishing a standard from a protocol

The anthology's three protocol documents are told apart by what happens
when you disagree with one.

Disagreeing with a standard in this document means shipping something
that is not Peios.

Disagreeing with PSPK or PSPU means shipping a system built from
different parts — a different kernel subsystem, or a different set of
userspace components. That is a design choice, not a conformance
failure.

> [!NOTE]
> The consequence of the second and third properties together is that
> conformance is checked against the protocol, never against Mainline. A
> system that speaks a standard correctly conforms to it, whatever it
> runs behind the channel and however it reaches its answers.

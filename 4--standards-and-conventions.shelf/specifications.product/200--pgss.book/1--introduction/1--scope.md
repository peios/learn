---
title: Scope
description: What PGSS is, standards that Peios implements and another
  system could adopt, and the tests that separate a standard from a
  protocol.
---

This document defines the **Peios Generic System Standards (PGSS)**:
standards that Peios implements, written so that another system could
adopt them.

A standard belongs in this document when three things are true of it.

**It is useful outside Peios.** Another system could adopt the standard
without changing how the rest of that system works. A standard that
only makes sense given the Peios kernel, or given a particular Peios
component, belongs in PSPK or PSPU.

**It belongs to no implementation.** A PGSS standard describes a contract
between two roles, not the behavior of a particular program. Mainline
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

The anthology's three protocol documents are told apart by who could
use them.

A standard in this document stands alone. A system that is not Peios
can implement it and interoperate with every other implementation.

PSPK and PSPU describe how the parts of Peios fit together: the kernel
boundary, and the protocols between foundational userspace components.
They have little use outside a system built from those parts.

Placement is a judgment about where a standard is most useful, not a
rule that can be applied mechanically.

## What depends on these standards

No standard here is a test of whether a system is Peios. In practice a
system needs them all the same. They define mechanisms that many
separate components rely on, and a system that leaves one out cannot
expect software written for Peios to work with it.

> [!NOTE]
> The consequence of the second and third properties together is that
> conformance is checked against the protocol, never against Mainline. A
> system that speaks a standard correctly conforms to it, whatever it
> runs behind the channel and however it reaches its answers.

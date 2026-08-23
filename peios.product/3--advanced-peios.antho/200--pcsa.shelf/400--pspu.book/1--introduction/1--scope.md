---
title: Scope
description: What PSPU is — the protocols and interchange formats the foundational userspace components speak to each other — and why they are not conformance requirements.
---

This document defines the **Peios System Protocols Userspace (PSPU)**:
the protocols and interchange formats by which the foundational
userspace components of a Peios system agree with one another.

An interface belongs in this document when both of these hold:

- it is a contract between userspace parties, at least one of which is a
  component the system is built from rather than an application running
  on it; and
- the interface is public — a third party is expected to implement one
  side of it.

The parties need not exist at the same moment. A live protocol has two
processes in conversation; an interchange format has a producer and a
consumer that never meet, and the artifact between them carries the
contract. Both are in scope, because what makes something belong here is
that two independently written parties must agree on it.

## These protocols are not conformance requirements

A system that does not offer a protocol in this document is still Peios.
The components that speak these protocols are one answer to a problem,
not the definition of the platform; a system that solves the same problem
with different components conforms exactly as well.

They are specified because they are *public* even so. A third party
writing a component to plug into one side of one of these protocols needs
the contract written down, and needs it to stay put. What they are not is
a bar anyone must clear.

For each interface, this document covers:

- for a live protocol: the channel, its direction, which party connects
  to which, message framing and encoding, the messages exchanged, and
  the shape of a conversation
- for an interchange format: the layout of the artifact, how it is
  identified and versioned, and how a consumer validates one it receives
- how a party announces itself or is identified, and how its counterpart
  establishes what it is and what it may speak for
- the rules under which the format may be extended
- what each party must declare about itself, and what its counterpart
  validates rather than believes
- the conformance requirements for each role

This document does not cover:

- Standards a system MUST implement to be Peios — defined in PGSS
- Protocols spoken across the kernel boundary — defined in PSPK
- The binary structures these interfaces carry — defined in PCDS
- How a component stores its data, reaches the answers it gives, or
  produces the artifacts it emits — its own design
- Which counterparts a system is configured to trust, and how that
  configuration is expressed — the consuming component's own design
- Administering a component's contents — its own design

The fourth of those is the point of the whole document. A component is
asked a question and gives an answer, or is asked for an artifact and
produces one; how it arrives there is exactly what different components
exist to do differently.

## Stability

Publication here is a commitment that the contract is written down and
will not change out from under an implementation. Each specification
states its own rules for extending its wire or file format; those rules
are the supported way for an interface to grow.

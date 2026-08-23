---
title: Scope and Roles
description: The KMES contract and its two roles — the kernel as sole producer, userspace as consumer — and the privilege that gates attachment.
---

This chapter specifies the contract between the Kernel Mediated Event
Subsystem and the userspace processes that consume the events it
produces.

Two roles participate.

The **producer** is KMES, a subsystem of the Peios kernel. It
constructs events, stamps them with metadata that a consumer cannot
forge, places them in per-CPU shared memory ring buffers, and notifies
sleeping consumers. There is one producer.

The **consumer** is a userspace process that maps one or more ring
buffers and reads events from them. The consumer role is publicly
implementable: any process holding the required privilege MAY attach,
and more than one consumer MAY attach to the same buffer at the same
time. A conforming consumer is the subject of the requirements in this
chapter.

This chapter covers:

- the binary layout of an event, which a consumer MUST parse
- the layout of a mapped ring buffer and the meaning of each metadata
  field
- how a consumer attaches, maps, and discovers the buffer set
- the protocol a consumer follows to drain events, to detect and
  account for loss, and to sleep and be woken
- the protocol a consumer follows when the producer replaces a buffer
- the memory ordering both roles rely on

This chapter does not cover:

- how KMES constructs, stamps, buffers, or overwrites events — the
  producer's internals are described in the Peios Kernel TRM
- the emission interfaces, by which a process or kernel subsystem
  produces an event rather than consuming one
- event type vocabulary, payload schemas, persistence, indexing, or
  querying — these are the concern of the event storage service
- the encoding of payload bytes beyond their being a single MessagePack
  value

## Producing versus consuming

Emission is not part of this contract. A process emits events by
calling the KMES emission system calls, which are an ordinary kernel
interface offered to any caller that holds the privilege — the kernel
computes the result and the caller reads it. Consumption is different:
the kernel deposits bytes in shared memory and depends on an
independently written program to interpret them correctly, to
sequence its reads against concurrent writes, and to notice when it
has fallen behind. That program's obligations have to be written down,
which is why they are here.

## What the kernel establishes for itself

A consumer maps one page that it can write: the consumer metadata
page. Everything the kernel reads from that page is advisory.

KMES reads exactly one field from consumer-writable memory, the
`need_wake` flag, and treats any nonzero value as set. The flag can
only cause KMES to perform a wake that was not needed or to skip one
that was; it cannot affect the contents of the data region, the
producer metadata, the sequence numbering, or another consumer's view
of any of these. A consumer that corrupts the page — deliberately or
otherwise — degrades notification for consumers sharing that buffer
and nothing else.

Consumers MUST NOT rely on KMES validating anything else they write,
because KMES reads nothing else.

The reverse direction is stronger. The producer metadata page and the
data region are mapped read-only, and no privilege, capability, or
token grants a consumer write access to them. Every identity stamp in
an event header is captured by the kernel from kernel state at the
moment of the write; an emitting process cannot set, influence, or
suppress it. A consumer MAY therefore treat the identity fields of a
delivered event as authoritative.

## Privilege and the trust model

Attaching requires SeSecurityPrivilege, which is a very high-trust
privilege. Direct ring buffer access is not the ordinary way to
consume events: it grants an unfiltered view of every event on the
system, with no per-event access control. Ordinary consumers obtain
events from the event storage service, which enforces per-event
access control on top of this interface.

Because the consumer metadata page is shared by every consumer
attached to a buffer, a consumer holding SeSecurityPrivilege can
suppress notification for the others attached to that buffer. This is
accepted rather than defended against: the privilege required to
attach at all is higher than the privilege this would subvert.

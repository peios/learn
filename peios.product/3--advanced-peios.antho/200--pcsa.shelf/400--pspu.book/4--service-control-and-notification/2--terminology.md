---
title: Terminology
description: Terms this chapter defines for itself — service, job, operation and advisory — and the ones it borrows unchanged.
---

**Service.** A named unit of execution the manager supervises. Service
names are opaque to this chapter except for the character restriction in
§4.8.

**Job.** One process execution. A service that has been restarted has
had more than one job.

**Operation.** A requested state machine action on a service, with an
identity and a lifecycle of its own. Lifecycle commands do not act
directly; they create operations, and an operation is what a client
observes and waits on.

**Activation generation.** A counter the manager increments each time a
service begins starting. It distinguishes one incarnation of a service
from the next.

**Right.** A named permission on a service or on the manager itself,
represented as a bit in an access mask and evaluated against a Security
Descriptor. §4.7.

**Dependent-satisfying state.** A service state in which the services
that depend on the service may proceed. Which states these are is the
manager's design; that a state is or is not one of them is observable
through the state vocabulary.

**Terminal state.** For an operation, one of `completed`, `failed`,
`cancelled`, `merged` or `aborted`. An operation in a terminal state
does not change again.

**Frame.** One newline-terminated line on the control channel, carrying
exactly one JSON object.

**Datagram.** One message on the notification channel, carrying zero or
more `KEY=VALUE` lines and optionally file descriptors.

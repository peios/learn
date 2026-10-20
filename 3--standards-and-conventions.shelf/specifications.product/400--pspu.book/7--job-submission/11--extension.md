---
title: Extension
description: The jobs channel is extended under §4.21's rules — what may be added freely, what may not, and the two things that may never be added at all.
---

The jobs channel carries no version number, and is extended under the
rules of §4.21. They are not repeated; what follows is how they apply
here and what this chapter adds.

## What may be added

A **request field**, including a new definition field on `submit`. A
manager MUST ignore a field it does not recognise, so a submitter MAY
send one and MUST NOT depend on its effect.

A **job view field**. A client MUST ignore a field it does not
recognise.

A **command**, and the error codes and enumerated values that appear
only in responses to it, on the terms §4.21 gives: a client that never
sends the command is never exposed to them.

## What may not be added without a version

A **state**, a **cause**, a **progress unit**, or a **`for` value**
outside §7.B. A **command** changing what an existing command does. A
change to the **shape** of the job view. A new **error code** on an
existing command.

## What may never be added

Two things are excluded from extension by any means, because their
absence is a security property of the channel rather than a gap in
it:

- **An identity field.** A `submit` MUST NOT be able to name the
  principal the job runs as. Every job identity is one the kernel
  verified the submitter could convey (§7.5), and a field that named
  one would be a path around that verification.
- **A policy field.** A `submit` MUST NOT be able to ask for a
  restart, a dependency, a health check or a trigger. A job that needs
  policy is a service, and a service is defined where an administrator
  controls it.

A revision that wanted either would not be a revision of this channel.

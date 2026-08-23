---
title: The Two Document Classes
description: Specification or manual, decided by one test — how many independently written parties have to agree. Most subsystems split across both.
---

Every technical document in this corpus is either a **specification** or
a **technical reference manual**, and the difference is not a matter of
subject, length, or tone. It is a matter of how many independently
written parties have to reproduce the same computation in order to
agree.

- If one party computes something and everyone else calls it, that is a
  **manual**.
- If a second party must reproduce it identically, or the two produce
  divergent results, that is a **specification**.

## The sharper form of the test

A third party wanting to interact with something directly is *necessary*
but not sufficient. What makes something a specification is a second
**role** — a party whose behaviour the other side depends on.

A system-call surface has no second role. It has callers, and callers
are documented rather than specified. The question that settles it is
which party is *asking*: a registry source answers the kernel's
questions, and a package producer emits what a consumer validates, so
both of those are specifications. Nobody serves `mount(2)`, so that is a
manual.

## Most subsystems split

The expected outcome for any given subsystem is **both**: a
specification stating the contract, and a manual covering the nuances of
how one implementation fulfils it.

Binary signing is a specification because a third party can sign
binaries; the kernel's verification machinery behind it is a manual.
Security descriptor inheritance is a specification even though there is
one kernel, because the kernel does not propagate a descriptor change
and every userspace tool that propagates one has to agree. A package's
manifest schema is a specification; how a package manager decides which
of several candidates to install is a manual.

A subsystem whose only external surface is its own syscalls contributes
no specification at all, and that is a legitimate outcome rather than an
oversight.

## Consequences for the reader

A specification tells you what you may rely on. Its statements are
commitments, and an implementation that contradicts one has a defect.

A manual tells you what a component does. Its authority comes from the
software: where the two disagree, the software is right and the manual
is stale. A manual makes no stability commitment, and nothing in one is
a promise about a future version.

That difference is why the two classes are written so differently, and
why a reader must be able to tell at a glance which one is in front of
them (§4.2).

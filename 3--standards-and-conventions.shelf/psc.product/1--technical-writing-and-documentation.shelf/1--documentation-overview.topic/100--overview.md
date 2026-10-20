---
title: Overview
type: concept
description: Peios is documented in seven forms (learn, man pages,
  command-line help, regman, evman, technical reference manuals, and
  specifications), each with its own reader, its own job, and its own place
  when two of them overlap.
---

Peios documentation comes in seven forms. Each one has a different reader
and answers a different question. Learn explains and help summarizes; each
of the other five forms is the authority for its own kind of fact.

| Form | Reader | Answers |
|---|---|---|
| **Learn** | Anyone getting oriented | Why does this exist, and how does it fit together? |
| **Man pages** | Users, administrators, and developers at the interface | Exactly what does this command, file, call, or function do? |
| **Command-line help** | Anyone at a prompt who needs a reminder | What does this program accept? |
| **regman** | Anyone reading or changing configuration | What does this registry key mean, and what values are valid? |
| **evman** | Anyone reading the event stream | What does this event, or this field, mean? |
| **Technical reference manuals** | Developers of one specific component | How does this component work inside? |
| **Specifications** | Anyone implementing or consuming a shared protocol or format | What must be true? |

## Learn

High-level, educational documentation. Learn is what you read when you want
to understand something: concepts, how the pieces fit, and guides that walk
through a task. Developer guides, such as how to package an application or
how to emit events, are learn, not reference.

Learn can describe an interface, but it is never the authority for one. Where
it touches a flag, a key, or an event, it links to the form that owns it.

## Man pages

Thorough technical documentation, still centered on the user. A man page is
where every flag, exit status, file, and environment variable is recorded,
including the edge cases learn leaves out. If you have forgotten something,
you read the man page.

Man pages are also the API reference: section 2 for system calls, section 3
for library functions.

Some overlap with learn is inevitable, and the set includes pages adopted
from other projects. Adopted pages are patched wherever Peios behaves
differently from upstream. Peios does not ship inaccurate documentation.

## Command-line help

The text a program prints for `--help`: one line for each command,
argument, and option, and a pointer to the man page. Help is a summary of
the man page, never a replacement for it, and the two must agree. The same
rules cover the version and error messages a program prints.

## regman

regman owns the documentation of every registry key and value: its type,
default, valid range, and what it applies to. Other forms do not document
configuration inline; they point at the regman page.

## evman

evman owns the documentation of every event and every event field. A field
with no evman definition is not part of the platform's vocabulary, and no
component is allowed to emit it.

## Technical reference manuals

Thorough systems documentation for the developers of one specific component:
its internal design, data structures, and behavior. A TRM describes one
implementation.

## Specifications

Specifications for the protocols and formats shared across Peios. A
specification states a contract that more than one party relies on.

The line between a TRM and a specification: if a second implementation, or a
consumer on the other side of the boundary, would need to know it, it belongs
in a specification. If it is true only of this implementation, it belongs in
the TRM. TRMs cite specifications rather than restating them.

## When forms overlap

Every fact has one authority:

- **Interface details** (flags, exit statuses, files, calls) belong to the man
  page. Help summarizes them and must agree with it.
- **Registry keys** belong to regman, and **events** to evman, without
  exception.
- **Shared contracts** belong to the specification, which wins over any TRM.
- **Learn** explains and links; it is never the source to quote.

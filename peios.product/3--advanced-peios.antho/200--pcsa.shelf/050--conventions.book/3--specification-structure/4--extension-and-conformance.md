---
title: Extension and Conformance
description: How a format or protocol chapter states the way it may grow, and how a book states what conformance to it requires.
---

## Extension

A chapter specifying a wire format, a file format, or a protocol SHOULD
close with an extension article stating how the thing may grow.

An extension article SHOULD distinguish:

- **Additive changes**, which an implementation of the current version
  can ignore safely — a new optional field, a new entry in an
  open-ended set.
- **Changes requiring a version bump**, which it cannot — a new required
  field, a new value in a **closed** enumeration, any change to an
  algorithm the format has frozen.
- **Reserved space**, where the format deliberately leaves room, and
  what an implementation does when it encounters a value there.

A specification MUST state, for every enumeration it defines, whether
that enumeration is closed. An implementation cannot decide whether to
ignore or reject an unknown value without being told.

> [!NOTE]
> The test for whether a change is additive is not whether it is small.
> It is whether an implementation that ignores it still behaves
> correctly. An optional field whose absence changes what gets
> installed is not additive, however optional it looks.

## Conformance

A chapter SHOULD close with a conformance article summarising, per role
(§3.2), what that role must do. The article is a summary and MUST NOT
introduce a requirement stated nowhere else.

A conformance article SHOULD also state plainly **what conformance does
not require**. A reader who has just been given a list of obligations
benefits more from knowing where their freedom lies than from a longer
list.

> [!NOTE]
> The useful shape is: here is what you must reach the same answer on
> as everybody else, and here is everything you are free to do
> differently. A specification that never says the second half reads as
> though it constrains the whole implementation, and implementers
> respond by over-constraining themselves or by ignoring it.

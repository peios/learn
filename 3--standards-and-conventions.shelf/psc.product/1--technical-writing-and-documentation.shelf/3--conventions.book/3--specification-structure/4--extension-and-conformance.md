---
title: Extension and Conformance
description: How a format or protocol chapter states the ways it can
  grow, and how its closing conformance article summarizes each role's
  obligations and freedoms.
---

A format or protocol chapter closes with two articles: one saying how
the thing it specifies can grow, and one summarizing what conformance
requires of each role.

## Extension

A chapter specifying a wire format, a file format, or a protocol SHOULD
close with an extension article stating how the thing can grow.

An extension article SHOULD distinguish three kinds of change:

- **Additive changes.** Changes an implementation of the current version
  can ignore safely, such as a new optional field or a new entry in an
  open-ended set.
- **Changes requiring a version bump.** Changes it cannot ignore, such
  as a new required field, a new value in a closed enumeration, or any
  change to an algorithm the format has frozen.
- **Reserved space.** Room the format deliberately leaves, and what an
  implementation does when it encounters a value there.

A specification MUST state, for every enumeration it defines, whether
that enumeration is closed. An implementation cannot decide whether to
ignore or reject an unknown value without being told.

> [!NOTE]
> The test for whether a change is additive is not whether it is small.
> It is whether an implementation that ignores it still behaves
> correctly. An optional field whose absence changes what gets
> installed is not additive, however optional it looks.

## Conformance

A chapter SHOULD close with a conformance article summarizing, per role
(§3.2), what that role must do. The article is a summary and MUST NOT
introduce a requirement stated nowhere else.

A conformance article SHOULD also state plainly what conformance does
not require. A reader who has been given a list of obligations
benefits more from knowing where their freedom lies than from a longer
list.

> [!NOTE]
> The useful shape has two halves: what an implementation must agree on
> with everybody else, and everything it is free to do differently. A
> specification that never says the second half reads as though it
> constrains the whole implementation, and implementers respond by
> over-constraining themselves or by ignoring it.

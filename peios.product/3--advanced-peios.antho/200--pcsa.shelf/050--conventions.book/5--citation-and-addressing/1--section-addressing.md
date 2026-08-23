---
title: Section Addressing
description: Where a § number comes from — the book's own structure — and how stable it is across revisions.
---

Any part of any book in this corpus is addressable with the `§` symbol
followed by a number derived from the book's structure.

| Form | Means | Example |
|---|---|---|
| `§N` | Chapter N | PSPU `§5` |
| `§N.M` | Article M of chapter N | PSPU `§5.23` |
| `§N.A` | Appendix A of chapter N | PSPU `§5.A` |
| `§A` | Appendix A of the book | the peipkg TRM `§A` |

The examples are qualified because a bare `§` reference means "this
book" (§5.2). Within this document, `§2.1` is the RFC 2119 article and
`§A` is the normative-reference list.

## Where the numbers come from

Chapter and article numbers derive from the ordering of directories and
files, and are supplied by the renderer. An author does not write them
into the text.

A chapter appendix — a file whose name marks it as an appendix, within a
chapter directory — is lettered rather than numbered, and cited in the
form `§N.A`. A **book-level** appendix, at the book root, is rendered as
"Appendix A" and is cited by its letter alone, with no chapter component
at all.

The two are easy to confuse and produce silently wrong references. An
author adding a second appendix to a chapter SHOULD check the rendered
index before relying on the citation.

## Stability

Section numbers are positional. Inserting a chapter shifts every
following chapter; inserting an article shifts the rest of its chapter.

A book that other documents cite SHOULD therefore append rather than
insert, where the choice exists. Where a restructure is unavoidable,
every inbound reference has to be revalidated (§5.4).

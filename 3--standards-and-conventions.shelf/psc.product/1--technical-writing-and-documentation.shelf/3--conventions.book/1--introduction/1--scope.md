---
title: Scope
description: The two classes of technical document this book governs, what
  it leaves to other documents, and how it relates to Core Style.
---

This document defines how the technical documents of Peios are written
and how they are read. It governs two classes of document:

- **Specifications.** The PCDS, PGSS, PSPK, and PSPU books, which state
  what must be true for a Peios system and for the parties that
  interoperate with one.
- **Technical reference manuals.** The per-component books that describe
  exhaustively how one piece of Peios actually behaves.

Together, the specifications and the technical reference manuals are the
corpus this book refers to.

It covers normative language, the structure a document of each class
takes, how any part of either is cited, and the style rules both share.

## What this document does not cover

This document does not cover four things:

- **The other forms of Peios documentation.** Learn, man pages, regman,
  and evman follow [Core Style](~psc/core-style) and their own form
  pages. Neither the normative apparatus of a specification nor the
  exhaustiveness of a reference manual applies to them.
- **Any behavior of Peios itself.** Nothing here specifies what a
  Peios system does. This document constrains documents.
- **The renderer.** The static site generator that builds these books
  supplies the chapter and article numbering this document's addressing
  scheme relies on, and is specified separately.
- **Editorial process.** How a document is reviewed, by whom, and when
  it is considered ready are project conventions rather than document
  conventions.

## Relationship to Core Style

This book sits in the Documentation shelf of Developing for Peios,
beside Core Style, and is the form-specific guide for specifications and
technical reference manuals. Core Style applies to specifications and
technical reference manuals too, except where this book says otherwise.
This book adds to it rather than repeating it, so an author reads Core
Style first and then the chapters here for the class they are writing.

This book departs from Core Style deliberately in five places:

- **Normative keywords.** A specification states each requirement with
  an RFC 2119 keyword (§2.1), and a technical reference manual uses
  none at all, in uppercase or in a lowercase form that reads as an
  obligation (§4.2).
- **Notes.** In a specification, a `[!NOTE]` callout marks informative
  text and carries the reasoning behind a rule, not only an aside (§2.2,
  §6.3).
- **Lowercase hexadecimal.** Hash values and byte sequences are written
  in lowercase hexadecimal, as they appear in the files and tool output
  a reader compares them with (§3.3).
- **Interim states.** A technical reference manual can describe the
  intended end state of deliberately provisional behavior, marked as
  such, as an exception to Core Style's rule against writing about time
  (§4.4).
- **This book's own rules.** This book is not a specification, but it
  states its rules with RFC 2119 keywords so that what it requires of a
  document is unambiguous (§1.3).

This book is not itself a specification: it defines no Peios behavior,
and no implementation conforms to it. What conforms to it are documents.

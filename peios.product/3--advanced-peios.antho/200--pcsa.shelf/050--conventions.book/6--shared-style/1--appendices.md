---
title: Appendices
description: What earns an appendix, why an appendix and the body must not duplicate each other, and how generated appendices are handled.
---

An appendix consolidates reference material that is defined in the body:
constants, limits, enumerated values, paths, configuration keys, event
types, wire vocabularies.

## Appendices and the body do not duplicate

Where a constant, table, or layout is defined in an appendix, the body
MUST reference it rather than restate it — and where it is defined in
the body, the appendix MUST reference *that*.

Exactly one of the two is the definition. The other points at it.

> [!NOTE]
> A value written down twice is a value that will eventually be written
> down differently. The appendix is where this bites hardest, because
> an appendix is exactly the kind of page that gets updated in isolation
> by someone who has not read the body — or skipped entirely by someone
> who has.

An appendix entry SHOULD carry a citation to the article that defines
what it lists, so that a reader who needs the semantics can get there in
one step.

## What earns an appendix

Material a reader looks *up* rather than reads: something they arrive at
knowing what they want.

A limits appendix is the clearest case. Every size bound, count cap, and
default in one table is genuinely more useful than the same figures
scattered across twenty articles, and the body articles then cite it
rather than repeating the number.

## Generated appendices

An appendix listing values that exist in source — an ABI table, a
constants list, an error enumeration — SHOULD be **generated from that
source rather than transcribed**, with a check mode that fails when the
committed file is stale.

> [!NOTE]
> The argument is empirical. In one case, a hand-written ABI appendix
> had every numeric value correct and a systematic error in the *names*.
> Transcription reproduces a wrong name faithfully and produces offsets
> nobody can cheaply re-check; generation cannot.

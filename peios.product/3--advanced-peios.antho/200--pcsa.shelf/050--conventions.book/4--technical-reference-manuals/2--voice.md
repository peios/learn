---
title: Voice
description: A manual describes and never requires — no normative keywords, the indicative mood, and the lowercase constructions that are the real hazard.
---

## No normative keywords

**A TRM MUST NOT use RFC 2119 keywords.** Not uppercase, and not in the
lowercase constructions that read as obligation.

This is the one rule in this chapter with no exceptions, because it is
what makes the class a class. A manual describes; it does not require.
A reader must be able to tell, from the first paragraph of any document
in this corpus, whether they are being told what something does or what
they must do.

## The indicative mood

Write what the component does.

| Not this | This |
|---|---|
| The daemon MUST reject a malformed request | The daemon rejects a malformed request |
| A client SHOULD retry after a timeout | A client that times out can retry |
| The cache MAY be discarded | The cache can be discarded at any time |
| Callers must hold the lock | Callers hold the lock |

The third and fourth rows are the ones that catch people. "May" and
"must" survive into descriptive prose easily, because an author
describing something real slips into obligation without noticing —
particularly when the source material was a specification.

## Lowercase keywords are the actual hazard

Uppercase keywords are trivially caught by searching. Lowercase ones are
not, and they are far more common: a conversion from specification prose
typically leaves a dozen or more.

An author SHOULD search a finished manual for lowercase `must`,
`should`, `shall`, `may not`, and `must not`, and rewrite every instance
that reads as a requirement. Idiomatic uses survive — "what the content
should be", "two files that cannot both be present" — and the test is
whether a reader could mistake the sentence for an obligation.

> [!NOTE]
> A validator that flags documents *lacking* normative keywords is
> useless here, and worse than useless if it is trusted: for a manual
> the signal is inverted. The check has to be run deliberately and in
> the opposite direction.

## Register

Plain declarative prose, addressed to a competent engineer. Not tutorial
and not chatty. A manual SHOULD assume its reader knows the platform and
wants the specifics.

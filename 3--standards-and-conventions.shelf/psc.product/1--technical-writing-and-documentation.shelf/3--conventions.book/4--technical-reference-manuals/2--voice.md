---
title: Voice
description: Why a technical reference manual describes and never
  requires, covering normative keywords, the indicative mood, lowercase
  keyword hazards, and register.
---

A technical reference manual (TRM) describes what a component does. Its
voice follows from that: it never states a requirement, in any form.

## No normative keywords

A TRM MUST NOT use RFC 2119 keywords, either in uppercase or in the
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
"must" survive into descriptive prose readily, because an author
describing something real slips into obligation without noticing,
particularly when the source material was a specification.

## Lowercase keywords are the actual hazard

Uppercase keywords are trivially caught by searching. Lowercase ones are
not, and they are far more common: a conversion from specification prose
typically leaves more than 10.

<!-- lint-disable words -->
An author SHOULD search a finished manual for lowercase `must`,
`should`, `shall`, `may`, and `must not`, and rewrite every instance
that reads as a requirement. Every `may` is rewritten, because
[Core Style](~psc/core-style) allows no lowercase "may" in prose. Idiomatic uses of the others
survive, such as "what the content should be," and the test is whether
a reader could mistake the sentence for an obligation.
<!-- lint-enable words -->

> [!NOTE]
> A validator that flags documents for lacking normative keywords is
> useless here, and worse than useless if it is trusted: for a manual
> the signal is inverted. The check has to be run deliberately and in
> the opposite direction.

## Register

A manual is plain declarative prose for a competent engineer, neither
tutorial nor chatty. It describes the component and does not address
the reader as "you." A manual SHOULD assume its reader knows the
platform and wants the specifics.

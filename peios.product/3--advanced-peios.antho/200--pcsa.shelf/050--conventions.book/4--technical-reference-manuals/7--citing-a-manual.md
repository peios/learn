---
title: Citing a Manual
description: The reverse direction — when a specification may defer to a manual, how the deferral must read, and KACS as the standing case.
---

§4.6 covers the ordinary direction: a manual cites the contract it
implements. The reverse direction needs a rule of its own, because a
specification that defers to a manual has given something up, and a
reader is entitled to know that it did.

## When it is allowed

A specification MAY cite a manual for material it deliberately does not
specify. It MUST NOT cite one for material within its own scope.

The test of §1.2 decides which case applies. If a second, independently
written party must reproduce the behaviour, it is contract — and a
citation to a manual there is a specification failing at its job, since
the other party has no manual for their own implementation. If no
second party is expected to reproduce it, because the component is
Peios' alone and is described rather than standardised, then the manual
is the only document that holds the material, and naming it beats
implying a standard exists somewhere.

## Say that it is a deferral

A specification citing a manual MUST make the deferral legible rather
than let it read as an ordinary cross-reference. "Described in the
Peios Kernel TRM §3.8" says what it is; "see §3.8" does not.

Where a scope article excludes a whole area to a manual, it SHOULD say
why once, in that article, rather than re-arguing it at each citation
site. The sites then only need to name the article.

## The standing case

KACS is the one that recurs. Peios' access-control implementation is
described in the Peios Kernel TRM §3 and is not separately specified,
so PCDS — which specifies the structures KACS consumes — defers to that
manual wherever a structure's meaning depends on what KACS does with
it. PCDS §1.1 records the arrangement; the individual citations name
the articles.

> [!NOTE]
> This is not licence to let a specification thin out over time. Each
> deferral is a decision that a given area will not be standardised,
> and the scope article is where that decision is visible. A citation
> to a manual appearing anywhere else, without a scope article behind
> it, is a defect.

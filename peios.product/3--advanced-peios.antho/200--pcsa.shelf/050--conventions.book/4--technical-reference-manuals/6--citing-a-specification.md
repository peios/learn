---
title: Citing a Specification
description: A manual cites the contract it implements rather than paraphrasing it, and adds what only an implementation can — order, limits, and choices.
---

Where a component implements a published contract, its manual cites the
contract rather than restating it.

## Cite, do not paraphrase

A manual SHOULD state that the contract exists, name where it is, and
describe what *this implementation* does about it:

> A dependency is satisfied by a candidate when the conditions of
> PSPU §5.21 hold. Three consequences of those rules shape how
> peipkg behaves.

A manual MUST NOT restate the contract's normative content in
descriptive prose. A paraphrase is a second copy that drifts, and
because the paraphrase carries no normative keywords, a reader cannot
tell which of the two they are supposed to rely on.

## What the manual adds

The nuances of one implementation: the order it does things in, the
limits it applies, what it does where the contract leaves a choice, and
what it does not implement.

A manual is the right place to say that a component is more restrictive
than the contract requires, or that it makes a choice the contract
leaves open. Those are facts about the software, not comparisons against
it.

## Where the split falls

The recurring question is whether a given fact belongs in the manual or
in the specification, and the test in §1.2 answers it: if a second
independently written party must reproduce it, it is contract.

Worked, from one component: what satisfies a dependency is contract;
which of several satisfying candidates gets chosen is implementation.
The schema of a declaration is contract; the command-line flag that
overrides it is implementation. The layout of an artifact is contract;
where the tool keeps its own database is implementation.

> [!NOTE]
> The most reliable way to settle a borderline case is to read the
> target specification's own scope article. It states what that book
> excludes, and it has overturned a placement more often than any
> argument from first principles.

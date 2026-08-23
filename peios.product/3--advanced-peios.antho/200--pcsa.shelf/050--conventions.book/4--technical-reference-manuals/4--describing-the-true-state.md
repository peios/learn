---
title: Describing the True State
description: A manual describes what the component does now, without narrating its divergences from a specification and without writing around them.
---

A TRM describes what the component does now. This has a consequence that
authors reliably find uncomfortable, and it is worth stating directly.

## Divergences are not narrated

**A TRM MUST NOT frame anything as a difference between itself and a
specification.** No "the specification requires X but the implementation
does Y", anywhere, in any form.

Where an implementation does not satisfy a contract, that is a defect.
It is recorded as one, in the project tracker, against the work that
would fix it — and the manual simply describes what the software does.

> [!NOTE]
> The reason is that a manual written as a divergence log rots into a
> second changelog nobody maintains, and undermines itself while doing
> it: a reader who is told the document is describing something wrong
> stops trusting the parts that are describing something right.
>
> It is also the wrong audience. The person who needs to know about a
> divergence is whoever will fix it, and they are looking at the
> tracker, not at a reference manual.

## Which does not mean writing around it

Describing the true state is not the same as being vague about it. A
manual SHOULD state plainly what a component does *not* do, where a
reader would otherwise assume it did:

> peipkg does not check free space before it starts. Exhaustion is
> discovered when a write fails.

That sentence is descriptive, useful, and carries no comparison to any
contract. The distinction is between *what is absent* — which a reader
needs — and *what was promised* — which belongs in the tracker.

## Interim states

Where behaviour is deliberately provisional, a manual MAY say so and
describe the intended end state, provided it describes the current one
first and at greater length. A manual SHOULD NOT let a description of an
intention displace the description of what actually runs.

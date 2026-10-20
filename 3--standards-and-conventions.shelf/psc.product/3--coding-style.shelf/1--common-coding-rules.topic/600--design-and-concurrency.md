---
title: Design and Concurrency
type: reference
description: Control flow, review thresholds, shared code, concurrency, and
  performance.
---

## Control flow

Prefer guard clauses and early returns to handle invalid inputs, errors, and
special cases before the main path. Keep the main path shallow rather than
nesting it inside successive checks. There is no requirement to use a single
return point.

Use a shared cleanup path when resource management makes it clearer or safer.
Early returns must still release owned resources and locks correctly.

## Function size and nesting

Use soft numeric thresholds to prompt a review of function size and nesting,
not hard limits. When a threshold is exceeded, consider whether the function
still has a clear purpose and understandable control flow, and whether a
meaningful extraction or simpler structure would improve it.

Review a function when it exceeds either initial threshold:

- More than 50 nonblank, non-comment lines in its body.
- More than three nested control-flow levels.

For length, count physical body lines containing code, including
delimiter-only lines; exclude the function signature, blank lines, and
comment-only lines. Count a mixed code/comment line once. Do not compress
statements to reduce the count.

For nesting, the function body starts at level zero. Each nested conditional,
loop, switch/match, or exception-handling construct adds a level. An `else if`
chain or sibling switch/match arms are alternatives at the same level, not
successively deeper levels. Plain grouping braces do not add control-flow
levels. Assess nested functions and lambdas separately.

Do not split a cohesive function solely to satisfy a number. Crossing a
threshold alone is not an automatic CI failure.

## Shared code and duplication

Avoid duplication when repeated code represents the same concept or rule.
Share that behavior through a meaningful helper or abstraction so changes to
the common rule can be made consistently.

Similar-looking code does not necessarily represent the same idea. Allow
duplication when combining it would tie together unrelated behavior that needs
to change independently. Do not introduce a shared abstraction solely to
eliminate repeated lines.

## Background work

Give background work a clear owner, lifetime, and shutdown behavior. Define
how failures are handled. When the initiating component stops, stop its work
or deliberately transfer responsibility to an owner that remains alive.

For example, closing a window that started a download should either stop the
download or hand it to a longer-lived service. Do not leave work running
merely because its ownership or cleanup was forgotten.

## Locking

Keep locks held for as little work as practical while preserving correctness.
Avoid slow work and calls into unknown code while holding a lock where
possible. Document the acquisition order when multiple locks must be held, and
follow it consistently.

Holding a lock longer is appropriate when correctness requires it. Respect the
requirements of the particular lock and execution context; shortening a lock
hold must not expose inconsistent state or introduce races.

## Unsafe operations

Keep operations that bypass language safety checks in narrow, reviewable parts
of the code. Document why they are safe and the assumptions they depend on.
For a direct memory access, this includes the relevant guarantees about memory
lifetime and validity of the access.

Review the surrounding code that maintains those assumptions as well as the
unsafe operations themselves. A small unsafe block alone does not establish
safety if other code can invalidate its assumptions.

## Performance

Treat performance as a design concern from the outset, not an afterthought.
Choose suitable algorithms and data structures and account for known critical
paths while designing the implementation.

Permit and encourage minor to moderate increases in complexity proactively
when there is a clear reason to expect substantial relative performance gains,
especially on hot paths in critical components. A benchmark is not a
prerequisite for every such decision. Make the expected benefit and reasoning
clear; distinguish an anticipated improvement from a measured result.

Use measurements where practical to validate and refine performance decisions.
Require stronger evidence as the complexity and maintenance cost of an
optimization grow. Avoid elaborate speculative optimizations without adequate
justification. Do not require a benchmark for every straightforward
improvement or use the absence of measurements to excuse wasteful code.

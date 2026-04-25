---
title: Dependency Relationships
---

peinit supports four dependency relationship types. Each type
defines how two services interact during start, stop, and failure
scenarios.

## Requires

A hard dependency. If service A `Requires` service B:

**Start:** B MUST satisfy A's dependency (reach a satisfying state)
before A may start. If B is not yet started, peinit MUST start B
with transition cause DependencyStart. If B enters Failed, A MUST
transition to Failed with cause DependencyFailure without
attempting to start.

**Stop (explicit):** stopping B does not automatically stop A.
A continues running. This is a start-ordering constraint, not a
runtime coupling.

**Failure (runtime):** if B crashes at runtime while A is Active,
A is NOT affected (Requires is not BindsTo). A continues running.
B's restart policy handles B's recovery independently.

**Missing target:** if B does not exist (no service definition in
the registry), A MUST transition to Failed with cause
DependencyFailure. Missing Requires targets are detected at graph
validation time.

## Wants

A soft dependency. If service A `Wants` service B:

**Start:** peinit starts B before A (with transition cause
DependencyStart) if B exists and is not Disabled. If B fails to
start or does not exist, A starts anyway.

**Stop:** no effect. A and B are independent at runtime.

**Failure:** no effect. B's failure does not propagate to A.

Wants is for best-effort ordering -- "start this first if you can,
but I'll work without it."

## BindsTo

A runtime coupling. If service A `BindsTo` service B:

**Start:** identical to Requires -- B MUST satisfy before A starts.
If B is not yet started, peinit starts B with transition cause
DependencyStart.

**Stop:** if B stops (for any reason -- explicit stop, conflict,
crash, shutdown), A MUST stop as well. peinit transitions A to
Stopping with cause BindsToPropagation.

**Recovery:** when B returns to Active after a failure, peinit
MUST automatically restart any service that is in Failed state
with cause BindsToPropagation from B's stop. This is reactive,
not polled -- peinit watches B's state transitions. BindsTo
recovery restarts MUST NOT consume the restart budget -- the
dependent did not fail on its own, it was stopped because its
binding target stopped.

BindsTo implies Requires. A service definition MAY list both for
clarity, but BindsTo alone is sufficient. If a service lists
both BindsTo and Requires for the same target, the BindsTo
semantics apply.

## Conflicts

Mutual exclusion. If service A `Conflicts` with service B:

**Start A while B is Active:** peinit MUST create a stop
operation for B (source: ConflictResolution) and transition B to
Stopping with cause ConflictEviction before starting A. If B
refuses to stop within its StopTimeout, SIGKILL escalation
applies.

**Start B while A is Active:** peinit MUST create a stop
operation for A (source: ConflictResolution) and transition A to
Stopping with cause ConflictEviction before starting B.

Conflicts are symmetric. If A declares `Conflicts = ["B"]`, then
starting either one stops the other. B does not need to declare
the conflict reciprocally -- peinit MUST enforce the relationship
regardless of which side declared it.

**Both started simultaneously:** if the graph contains both A and
B as boot-triggered services and they conflict, graph validation
detects this as an unresolvable conflict. Both services are marked
Failed with cause ValidationError.

> [!INFORMATIVE]
> Conflicts is for true mutual exclusion (e.g., two services that
> bind the same port, or two implementations of the same role where
> exactly one must run). It is not for resource contention that can
> be solved by other means.

## Implicit ordering

Dependencies imply start ordering but not stop ordering (except
BindsTo). peinit starts dependencies before dependents. During
shutdown, peinit reverses the graph and stops dependents before
dependencies (§10.1). This reversal is derived
from the same graph, not from a separate stop-ordering
configuration.

## Self-references

A service MUST NOT declare itself in any dependency field. peinit
MUST reject self-referential dependencies at graph validation time
as a CycleDetected failure.

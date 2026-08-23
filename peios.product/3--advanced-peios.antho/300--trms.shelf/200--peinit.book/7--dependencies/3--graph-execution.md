---
title: Graph Execution
description: Starting everything whose dependencies are satisfied and repeating until nothing more can start — contexts, failure propagation and shutdown ordering.
---

Executing a graph means starting the services whose dependencies are all
satisfied, and doing it again each time something becomes satisfying,
until nothing is left.

```
execute_graph(graph, max_parallel):
    ready = services with no unsatisfied dependencies
    in_flight = 0

    while ready is not empty or in_flight > 0:
        while ready is not empty and in_flight < max_parallel:
            begin_start(ready.dequeue())
            in_flight += 1

        match wait_for_event():
            ServiceSatisfied(s):
                in_flight -= 1
                for each dependent of s:
                    if all its dependencies are satisfied:
                        ready.enqueue(dependent)

            ServiceFailed(s):
                in_flight -= 1
                propagate_failure(s)
```

`MaxParallelStarts` bounds the concurrency, counted per context as the
members currently running.

## Execution contexts

A graph execution is a retained object, not a transient loop. peinit
holds a **context** carrying its members, their dependencies and their
status, and there are two kinds: one boot context built from the boot
plan, and an on-demand context per explicit start, built from that
service's validated transitive closure.

Both use the same scheduler, the same satisfaction rules, the same
failure propagation and the same parallelism, but they are distinct
runtime objects — which matters because they can overlap.

An operation is associated with **every** context that created or
adopted it. One operation can belong to more than one active on-demand
context: two administrators starting different services that share a
dependency both end up merged into the same already-starting operation
for it, and both contexts need to hear how it turns out.

So when a pre-start outcome is terminal for an operation, peinit
dispatches the corresponding graph event once **per associated
context**. An operation with no associated context completes or fails
normally, and its waiters are notified, but no graph event is
dispatched.

A member whose dependent resolves without ever needing it is **pruned**
— a dormant sub-tree is cancelled rather than started, so an on-demand
start that turns out not to need half its closure does not start that
half.

Contexts are not retired. A context and its operation associations
persist for the lifetime of the process.

## Failure propagation

When a service enters Failed during graph execution:

1. Everything that `Requires` or `BindsTo` it transitions to Failed with
   cause `DependencyFailure`.
2. Everything that `Wants` it is unaffected and starts normally.
3. Propagation is transitive: if A requires B and B requires C, and C
   fails, then B fails and then A fails.

## On-demand start

Starting a service explicitly resolves its dependencies first:

1. Collect the transitive `Requires` and `BindsTo` closure.
2. Collect the transitive `Wants` closure, best-effort.
3. Validate the sub-graph — cycles, missing targets.
4. Resolve conflicts, stopping whatever has to stop.
5. Start the sub-graph with the same parallel algorithm. Dependencies
   started this way carry cause `DependencyStart` and operation source
   `DependencyPropagation`.

A service already in a satisfying state — Active, Completed or Skipped —
is not restarted. Its dependency is already met.

The on-demand path treats a **disabled** hard-dependency target
differently from the boot path: where boot blocks the dependent, an
on-demand start includes the disabled target and starts it.

## Shutdown ordering

Shutdown reverses the graph: services with no dependents stop first,
services that everything depends on stop last, derived by reverse
topological sort from the same edges.

Only hard dependencies — `Requires` and `BindsTo` — contribute to the
ordering. A `Wants` dependent may therefore be stopped after its target.

The ordering is entirely emergent from what the definitions declare.
There is no floor and no pinning, so where the TCB services end up in
the wave order depends on their declared dependencies being right.

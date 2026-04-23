---
title: Graph Validation and Execution
---

## Validation

peinit MUST validate the dependency graph before executing it. The
graph is built from all boot-triggered services (during boot) or
from a specific service's transitive closure (on demand start).
Validation runs once per graph build. It is not incremental.

### Cycle detection

peinit MUST perform a topological sort of the graph. If the sort
fails, a cycle exists.

```
detect_cycles(graph) -> list of cycles:
    // Standard DFS-based cycle detection.
    // Returns all cycles, not just the first.
    for each unvisited node in graph:
        dfs(node, visited=[], stack=[])

    // Each cycle is a list of service names forming the loop.
```

All services in a detected cycle MUST be marked Failed with cause
CycleDetected. peinit MUST log the full cycle path (e.g.,
"dependency cycle: A -> B -> C -> A") so the administrator can
identify and break the cycle.

If any service in the cycle has ErrorControl=Critical, peinit MUST
downgrade to Safe mode (see the Boot Modes section). The cycle is
a configuration error -- rebooting would hit the same cycle. Safe
mode rebuilds the graph with a reduced service set, potentially
excluding the cycle participants.

### Missing dependency targets

For each Requires entry, the target MUST exist as a service
definition. If the target does not exist:

- The dependent is marked Failed with cause DependencyFailure.
- peinit logs: "service X requires Y, but Y is not defined."

For Wants entries, missing targets are silently dropped -- the
entry is ignored.

For BindsTo entries, missing targets are treated as missing
Requires (Failed with DependencyFailure).

For Conflicts entries, missing targets are silently dropped --
there is nothing to conflict with.

### Unresolvable conflicts

If two boot-triggered services conflict with each other, graph
validation detects this as unresolvable. Both MUST be marked
Failed with cause ValidationError. If either is Critical, Safe
mode applies.

### Validation warnings

The following conditions are logged as warnings but do not prevent
boot:

- A service uses Readiness=Alive and has dependents that use it as
  a Requires target. Alive readiness provides no guarantee that
  the service is functional before dependents start.

### Validation errors

The following conditions are validation errors. The service MUST
be marked Failed with cause ValidationError:

- A service has HealthCheck configured with timing parameters that
  violate the flap protection constraint
  (`HealthCheckRetries * HealthCheckInterval < RestartWindow`).
  See the Health Checks section.

## Graph execution

### Parallel start

After validation, peinit executes the graph by starting services
whose dependencies are all satisfied. Multiple services can start
concurrently up to MaxParallelStarts.

```
execute_graph(graph, max_parallel):
    ready_queue = services with no unsatisfied dependencies
    in_flight = 0

    while ready_queue is not empty or in_flight > 0:
        // Start eligible services up to concurrency limit.
        while ready_queue is not empty and in_flight < max_parallel:
            service = ready_queue.dequeue()
            begin_start(service)
            in_flight += 1

        // Wait for any in-flight service to change state.
        event = wait_for_event()

        match event:
            ServiceSatisfied(s):
                in_flight -= 1
                for each dependent of s:
                    if all dependencies of dependent are satisfied:
                        ready_queue.enqueue(dependent)

            ServiceFailed(s):
                in_flight -= 1
                propagate_failure(s)
                // Failed service's Requires dependents also fail.
                // Wants dependents are unaffected.
```

### Failure propagation

When a service enters Failed during graph execution:

1. All services that `Requires` the failed service MUST transition
   to Failed with cause DependencyFailure.
2. All services that `Wants` the failed service are unaffected --
   they start normally.
3. Failure propagation is transitive. If A requires B and B
   requires C, and C fails, then B fails (DependencyFailure), then
   A fails (DependencyFailure).

```
propagate_failure(failed_service):
    for each service that Requires failed_service:
        if service.state == Starting or service is queued:
            service.state = Failed
            service.cause = DependencyFailure
            propagate_failure(service)  // transitive
```

### On-demand start

When a service is started explicitly (not at boot), peinit MUST
resolve its transitive dependencies:

1. Collect all transitive Requires and BindsTo dependencies.
2. Collect all transitive Wants dependencies (best-effort).
3. Validate the sub-graph (cycle detection, missing targets).
4. Resolve Conflicts (stop conflicting services).
5. Start the sub-graph using the same parallel execution algorithm.
   Dependencies started as part of resolution use transition cause
   DependencyStart (operation source: DependencyPropagation).

Services already in a satisfying state (Active, Completed, Skipped)
do not need to be restarted -- their dependency is already met.

## Shutdown ordering

Shutdown reverses the dependency graph. Services that have no
dependents stop first; services that others depend on stop last.
The full shutdown sequence is defined in the Shutdown section. The
dependency graph provides the ordering:

```
shutdown_order(graph) -> ordered list:
    // Reverse topological sort.
    // Services with no dependents first.
    // Services with the most transitive dependents last.
```

The last services to stop are the TCB services that everything
depends on: eventd, authd, lpsd, and registryd (in that order).
registryd is the very last service stopped, mirroring its position
as the very first service started.

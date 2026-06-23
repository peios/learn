---
title: Dependencies and ordering
type: concept
description: "peinit has four dependency relationships — Requires, Wants, BindsTo, and Conflicts — and they decide start order, stop order, and how failure spreads. This page covers what each one does at start, stop, and failure; how peinit validates the graph for cycles and missing targets; how it starts services in parallel; and how shutdown reverses the whole thing."
related:
  - peios/peinit/the-service-lifecycle
  - peios/peinit/supervision
  - peios/peinit/boot-and-boot-modes
  - peios/peinit/shutdown
  - peios/peinit/jobs-and-operations
---

Services rarely stand alone. A web app needs its database; a network daemon needs the loopback interface up; two implementations of the same role must never run at once. peinit expresses all of this with four relationship fields — `Requires`, `Wants`, `BindsTo`, and `Conflicts` — that together decide the order services start in, what happens when one stops, and how a failure spreads to its neighbours.

The relationships are declared on the *dependent* (the service that needs something), naming the *target* (the service it needs) by name. `Conflicts` is the exception — it is symmetric, and one side declaring it is enough.

## The four relationships

### Requires — a hard dependency

If A `Requires` B:

- **Start.** B must reach a [satisfying state](~peios/peinit/the-service-lifecycle) before A starts. If B is not running, peinit starts it first (cause `DependencyStart`). If B fails, A is marked Failed with `DependencyFailure` and never even attempts to start.
- **Stop.** Stopping B does **not** stop A. Requires is a *start-ordering* constraint, not a runtime leash — A keeps running.
- **Runtime failure.** If B crashes while A is already Active, A is unaffected. B's own [restart policy](~peios/peinit/supervision) handles B's recovery.

Requires is the workhorse: "I need this to have started, and if it can't, neither can I."

### Wants — a soft dependency

If A `Wants` B:

- **Start.** peinit starts B before A *if* B exists and is not [Disabled](~peios/peinit/triggers-and-timers) — but if B fails to start, or does not exist, **A starts anyway.**
- **Stop / failure.** No effect either way. A and B are runtime-independent.

Wants is best-effort ordering: "start this first if you can, but I work without it."

### BindsTo — a runtime coupling

If A `BindsTo` B:

- **Start.** Identical to Requires — B must satisfy before A starts.
- **Stop.** If B stops for *any* reason — explicit stop, conflict, crash, shutdown — A is stopped too, transitioning to Stopping with cause `BindsToPropagation`.
- **Recovery.** When B returns to Active, peinit **automatically restarts** A (cause `BindsToRecovery`). This is reactive — peinit watches B's transitions — and it is **budget-exempt**: A did not fail on its own, so the restart does not count against its [budget](~peios/peinit/supervision).

BindsTo is Requires plus a runtime leash: "I need this to start, *and* I should not outlive it." It is the right choice for a sidecar that is meaningless without its principal. `BindsTo` implies `Requires`; listing both for the same target is harmless, and BindsTo semantics win.

### Conflicts — mutual exclusion

If A `Conflicts` with B:

- **Start.** Starting A while B is Active creates a stop operation for B (source `ConflictResolution`), evicting it (cause `ConflictEviction`) before A starts — and vice versa. If the loser will not stop within its `StopTimeout`, [SIGKILL escalation](~peios/peinit/shutdown) applies.
- **Symmetry.** Conflicts is two-way. If A declares `Conflicts=["B"]`, starting *either* stops the other; B need not declare it back.

Conflicts is for true mutual exclusion — two services binding the same port, or two implementations of one role where exactly one must run — not for ordinary resource contention.

### At a glance

| | Start order | Target failure stops dependent? | Target stop stops dependent? |
|---|---|---|---|
| **Requires** | target first; dependent fails if target fails | At start time only | No |
| **Wants** | target first if present; dependent starts regardless | No | No |
| **BindsTo** | target first; dependent fails if target fails | Yes (and auto-recovers) | Yes (and auto-recovers) |
| **Conflicts** | starting one evicts the other | n/a | n/a |

## Graph validation

Before peinit starts *anything*, it builds the dependency graph and validates it. Validation runs once per graph build — at boot for the whole boot graph, and per request for an [on-demand start](#on-demand-starts)'s transitive closure. It is not incremental.

**Cycles.** peinit topologically sorts the graph; if the sort fails, there is a cycle. Every service in the cycle is marked Failed with `CycleDetected`, and peinit logs the full path (`dependency cycle: A → B → C → A`) so you can find and break it. A service may not depend on itself — a self-reference is rejected as a cycle. If any service in the cycle is `ErrorControl=Critical`, peinit downgrades to [Safe mode](~peios/peinit/boot-and-boot-modes) rather than rebooting, because a reboot would just hit the same cycle.

**Missing targets.** What a missing target means depends on the relationship:

| Relationship | Missing or disabled target |
|---|---|
| `Requires` | Dependent marked Failed (`DependencyFailure`). |
| `BindsTo` | Treated as a missing Requires — Failed (`DependencyFailure`). |
| `Wants` | Silently ignored — the entry is dropped. |
| `Conflicts` | Silently ignored — nothing to conflict with. |

**Unresolvable conflicts.** If two *boot-triggered* services conflict with each other, there is no way to honour both, so both are marked Failed with `ValidationError`. As with cycles, if either is Critical, Safe mode applies.

**Warnings.** Some conditions are logged but do not block boot — most notably a `Readiness=Alive` service that others `Requires` (see [service types](~peios/peinit/service-types)). Warnings appear in the logs and do not change state.

**Validation errors.** Some conditions *do* fail the service — for example a health-check configuration that violates the [flap constraint](~peios/peinit/supervision). These mark the service Failed with `ValidationError`.

When more than one finding applies to the same service, peinit records a single primary cause by precedence — `CycleDetected` > `ValidationError` > `DependencyFailure` — but it logs *all* findings, so the primary cause never hides the others.

## Parallel start

After validation, peinit starts services whose dependencies are all satisfied, and it does so **in parallel** up to a configurable limit:

| Registry key | Default | Meaning |
|---|---|---|
| `Machine\System\Boot\MaxParallelStarts` | 10 | Maximum services starting concurrently. |

The scheduler is simple: every service with no unsatisfied dependencies is eligible; peinit starts up to `MaxParallelStarts` of them; as each one reaches a [satisfying state](~peios/peinit/the-service-lifecycle) its dependents become eligible and join the queue. The result is that independent subtrees of the graph come up at the same time, while ordering constraints are still honoured exactly.

> [!NOTE]
> Boot order is *emergent*, not hardcoded. The typical sequence — `eudev`, `lpsd`, `authd`, `eventd`, networking, then application and login services — is simply what the standard role definitions' dependencies produce. Change the dependencies and you get a different order. The platform daemons come up first because everything else, directly or transitively, requires them.

## Failure propagation

When a service enters Failed during graph execution, the failure spreads along `Requires` and `BindsTo` edges — and only those:

1. Every service that `Requires` the failed one transitions to Failed with `DependencyFailure`.
2. Every service that merely `Wants` it is **unaffected** and starts normally.
3. Propagation is **transitive**: if A requires B and B requires C, and C fails, then B fails, then A fails — each with `DependencyFailure`.

This is the payoff of the Requires/Wants distinction. A hard dependency failing takes its dependents down with it; a soft one failing is shrugged off. Choosing the right relationship is choosing how far a failure is allowed to travel.

## On-demand starts

When you start a service explicitly rather than at boot, peinit does the same graph work on a smaller scope — the requested service's transitive closure:

1. Collect all transitive `Requires` and `BindsTo` dependencies (and best-effort `Wants`).
2. Validate that sub-graph (cycles, missing targets).
3. Resolve `Conflicts` — stop anything that conflicts.
4. Start the sub-graph with the same parallel scheduler.

Anything already in a satisfying state (Active, Completed, Skipped) is left alone — its dependency is already met, so there is no needless restart. Dependencies pulled in this way start with cause `DependencyStart`. If two on-demand starts need the same dependency at once, their start operations [merge](~peios/peinit/jobs-and-operations) rather than racing.

## Shutdown reverses the graph

peinit does not need a separate stop-ordering configuration. [Shutdown](~peios/peinit/shutdown) simply **reverses** the dependency graph: services with no dependents stop first, and services that others depend on stop last. A service is never stopped until everything that `Requires` or `BindsTo` it has already stopped.

The very last services to stop are the TCB daemons everything rests on — `eventd`, then `authd`, then `lpsd`, then `registryd` — with `registryd` stopped dead last, mirroring its position as the first service ever started. The full shutdown sequence is in [Shutdown](~peios/peinit/shutdown).

## Where to start

To see the states services move through as they start and stop in order, read [The service lifecycle](~peios/peinit/the-service-lifecycle).

To understand how a target's failure interacts with the dependent's own restart policy, read [Keeping services running](~peios/peinit/supervision).

To follow how dependency-driven starts appear as operations, read [Jobs and operations](~peios/peinit/jobs-and-operations).

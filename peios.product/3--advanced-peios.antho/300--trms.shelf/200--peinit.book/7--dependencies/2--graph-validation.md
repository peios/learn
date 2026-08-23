---
title: Graph Validation
description: peinit validates the dependency graph before executing it — cycles, missing targets, and the errors and warnings it produces.
---

peinit validates the dependency graph before executing it. Validation
runs once per graph build — at boot, on an on-demand start's transitive
closure, and on a reload-config — and is never incremental.

## Cycles

peinit topologically sorts the graph; if the sort fails, a cycle exists.
Detection returns **all** cycles rather than stopping at the first: each
detected cycle's members are removed and the search re-run until the
graph is clean.

Every service in a cycle is failed with cause `CycleDetected`, and the
cycle path is logged so an administrator can see what to break.

If any service in a cycle is Critical, peinit downgrades to Safe mode
(§2.6) rather than rebooting. The cycle is a configuration error, and
rebooting would find it again.

## Missing targets

| Relationship | A missing target means |
|---|---|
| `Requires` | The dependent is failed with `DependencyFailure`. |
| `BindsTo` | The same — treated as a missing `Requires`. |
| `Wants` | Silently dropped. |
| `Conflicts` | Silently dropped. |

Detection is a Full-mode behaviour. In Safe mode a hard-dependency
target that is missing, disabled, or not Safe-mode-eligible does not
block the dependent, which is started with the dependency unmet.

## Validation errors

A service that hits one is failed with cause `ValidationError` and never
started:

- The flap constraint,
  `HealthCheckRetries × HealthCheckInterval < RestartWindow` (§5.6).
- An invalid timer calendar expression (§9.1). This one is checked
  across every definition, not only those in the graph.
- Two boot-triggered services that conflict with each other. Both are
  failed. Safe mode applies if either is Critical.

## Validation warnings

Logged, and do not prevent boot:

- A service using `Readiness=Alive` that something else depends on
  hard. `Alive` readiness means the process exists, which is no
  guarantee it is functional, so anything waiting on it is waiting on
  the wrong thing.

## Multiple findings

A service can attract more than one finding in one pass — being both in
a cycle and missing a `Requires` target, say. The runtime state records
a single primary cause, chosen by precedence:

1. `CycleDetected`
2. `ValidationError`
3. `DependencyFailure`

The precedence affects only which cause is stored. Every other finding
for the service is retained beside it, in discovery order, and the
operation's failure message enumerates all of them:

```
CycleDetected: dependency cycle a -> b -> a (also: ValidationError:
health check interval exceeds the restart window) [2 findings]
```

The primary comes first and unqualified, so a service with one finding
reads exactly as it always did. A higher-precedence finding arriving
later demotes the previous primary rather than deleting it — breaking
the cycle should not be what it takes to discover the second fault.

Every finding is also emitted as its own `graph.validation_error` KMES
event, carrying `phase: "boot"`. The console lines are for whoever is
watching the boot; the events are the account that survives it.

`HardDependencyBlocked` — blocked *because a dependency is blocked* —
gets its own `finding` value rather than being reported as a missing
dependency, which would claim the target does not exist when it does.
It has no reload-path equivalent, because reload rejects wholesale
instead of propagating a block.

The reload path behaves differently, because its consequence is
different. Validation there accumulates every finding, encodes each as
its own event under `phase: "reload_config"`, and then rejects the
**entire reload** — the previous generation stays live and the findings
return to the caller (§10.4). Boot marks individual services and
continues; reload reports everything and changes nothing.

Both use the same event type deliberately: one consumer filter catches
validation problems in either regime, and `phase` says which.

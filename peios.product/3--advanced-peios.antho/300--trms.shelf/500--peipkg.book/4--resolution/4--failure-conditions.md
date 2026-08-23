---
title: Failure Conditions
description: Every condition that makes resolution produce no plan, each with a machine-readable reason and the package it names.
---

Resolution fails, producing no plan, when any of the following holds.
Each failure names a machine-readable reason and a detail identifying
the packages or constraints involved.

| Condition | Meaning |
|---|---|
| **Unsatisfiable** | A package in the candidate plan has a dependency no available package satisfies |
| **Conflict** | Two packages in the proposed resulting set trigger a conflict against each other |
| **Architecture mismatch** | A package in the plan is built for neither the system's primary architecture nor `noarch` |
| **Version regression** | An operation would move a package backwards without authorisation |
| **Cycle** | A dependency cycle the resolver cannot break by ordering |
| **Too complex** | The resolver's step budget was exhausted |

## Conflicts reject rather than cascade

A conflict fails the plan. peipkg does not offer to remove the
conflicting package to make room, which is why the cross-repository
conflict guard of §3.7 has nothing to gate: a low-trust package cannot
cause a high-trust one to be uninstalled as a side effect, because it
cannot cause anything to be uninstalled.

## Cycles are detected after provides resolution

Cycle detection runs on the graph that remains once `provides` entries
have been substituted for the dependency names they satisfy. A cycle in
the raw name graph that disappears once `provides` is resolved is not an
error.

## Bounded work

The forward walk carries an explicit step budget and stops with a "too
complex" rejection when it is exhausted, so a pathological dependency
graph cannot spin indefinitely. The algorithm itself is greedy and does
not backtrack, so it is polynomial in the size of the available set
regardless.

The consistency and planning passes that run after the walk are not
covered by the step budget. They are polynomial too, but on a very large
available set they are where the time goes.

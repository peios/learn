---
title: Satisfaction
description: When a candidate satisfies a dependency — direct names and provides, constraints, roles as goals, and the architecture qualifier.
---

A dependency is satisfied by a candidate when the conditions of PSPU
§5.21 hold: the name matches directly or through `provides`, any
constraint is met by the appropriate version, the architecture qualifier
is met, and the candidate is in the dependency's root.

Three consequences of those rules shape how peipkg behaves.

## A goal may name a role

An install goal is satisfied under the same conditions as a dependency,
with the goal's name in place of the dependency's. An operator may
therefore ask to install `sh`, `cc`, or `coreutils` and receive whatever
package provides it.

When a goal is satisfied by a candidate whose name differs from the one
the operator typed, peipkg reports the substitution. This is a notice
rather than an authorization: the operator is told, but an unattended
run is not blocked.

> [!NOTE]
> Reporting matters because the operator asked for one name and received
> a package with another. Reproducibility is not at stake — a consumer
> that records its resolved closure, as an image composition does, pins
> the chosen package, so the substitution is decided once rather than
> re-decided on every build.

A goal already satisfied by an installed *provider* is not recognised as
satisfied: peipkg checks whether the goal's name is present, not whether
something provides it. Asking to install a role that an installed
package already provides therefore installs a second provider.

## Upgrade and remove are name-only

An install goal may resolve through `provides`. An upgrade, a downgrade,
and a removal do not: they act on a package already installed under a
specific name, and resolving them through `provides` would let an
upgrade substitute a different package for the one the operator named.

## The architecture qualifier

The only qualifier value is `any`, and anything else is rejected. `any`
means the candidate's architecture equals the depending package's
effective architecture, or is `noarch`.

For a `noarch` depender the effective architecture is the system's
primary architecture — a script's dependency on its interpreter resolves
against the concrete system being assembled. peipkg applies that rule
when checking a plan for consistency. It does not apply it while
selecting a candidate for a `noarch` package's dependency, where the
architecture test is skipped entirely.

The visible consequence is a plan that could have been satisfied being
rejected instead: a foreign-architecture candidate wins selection, and
the consistency check then rejects the whole resolution rather than the
one candidate.

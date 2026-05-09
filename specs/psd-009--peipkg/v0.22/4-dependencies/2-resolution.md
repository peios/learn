---
title: Resolution
---

Dependency resolution is the procedure by which a package
manager, given a set of target packages to install or
upgrade, computes the complete set of packages to install,
upgrade, or remove on the target system.

This section defines the semantic requirements that a
conformant resolver MUST satisfy. The exact algorithm is
left to the implementation, provided the requirements are
met.

## Inputs

A resolution operation takes the following inputs:

- The **target set**: zero or more requested operations
  (install package P, upgrade package P, remove package P).
- The **installed set**: the set of packages currently
  installed on the system, with their versions and
  architectures.
- The **available set**: the union of all packages listed in
  configured repository indexes (§6.2, §6.3), each annotated
  with the repository it came from.

## Output

A resolution operation produces either:

- A **plan**: an ordered list of operations (install, upgrade,
  remove) that, if applied to the installed set, satisfies
  the target set without violating any constraint.
- A **rejection**: an error explaining why no satisfying plan
  exists.

A plan MUST be partial-ordered such that for every install
operation, all of that package's dependencies are present in
the installed set or scheduled to be installed earlier in the
plan.

## Satisfaction

A dependency is *satisfied* by a candidate package when ALL
of the following hold:

1. The candidate's name equals the dependency's `name`, OR
   the candidate has an entry in its `provides` array whose
   name equals the dependency's `name`.
2. If the dependency has a `constraint`, the candidate's
   version (or, when matched via `provides`, the
   provides-entry's `version`) satisfies the constraint per
   §2.2.6.
3. The candidate's architecture matches the dependency's
   `arch` qualifier per §4.1.3.

A conflict is *triggered* by a candidate package when the
same conditions hold with respect to a `conflicts` entry.

## Candidate selection

When multiple available packages satisfy a dependency, the
resolver MUST select among them deterministically using the
following rules in order:

1. **Architecture match preferred over noarch**: A candidate
   whose architecture exactly matches the system's primary
   architecture is preferred over a `noarch` candidate of
   the same name.
2. **Same-repository `provides` preferred (bounded)**:
   When the dependency is being resolved for a
   depending package D, and a candidate from D's same
   repository satisfies the dependency (whether by
   name match or via `provides`), that candidate is
   preferred over a cross-repository candidate ONLY
   when D's repository has a priority equal to or
   higher than the cross-repository alternative.
   When D is from a lower-priority repository than
   the cross-repository candidate, this rule does
   NOT apply; rule 3 (higher repository priority)
   selects the cross-repository candidate. This
   prevents a low-trust depending package from
   pulling in low-trust transitive dependencies that
   shadow higher-trust alternatives.
3. **Higher repository priority preferred**: A candidate from
   a higher-priority repository is preferred over one from a
   lower-priority repository (repository priority is
   defined in §6.5).
4. **Higher version preferred**: A candidate with a higher
   version (per §2.2.6) is preferred.
5. **Higher peios revision preferred** (already implied by
   rule 4, but retained for clarity).

When the chosen candidate satisfies the dependency via
`provides` from a lower-priority repository AND a
higher-priority repository contains a name-matching
package whose constraint check failed, the package
manager MUST surface the substitution to the operator as
a "low-trust-repo provides for high-trust-repo's role"
event and require explicit operator confirmation
(§7.6.6) before applying the resolution. This mirrors
the explicit-confirmation requirement for non-official-
repo `replaces` (§6.5.7).

Rule 1 ensures arch-specific builds are favoured when
available. Rule 2 ensures user-controlled repo priority is
respected. Rules 3 and 4 select the freshest version when
multiple satisfy.

## Failure conditions

A resolution operation MUST fail and produce no plan if any
of the following holds:

1. **Unsatisfiable dependency**: A package in the candidate
   plan has a dependency for which no available package
   satisfies all the satisfaction conditions (§4.2.3).
2. **Active conflict**: Two packages in the proposed
   resulting installed set (current installed minus removed
   plus added) trigger a conflict against each other.
3. **Architecture mismatch**: A package in the proposed plan
   has an architecture that is neither the system's primary
   architecture nor `noarch`.
4. **Version regression rejected by user**: An operation
   would result in a package's version going backward
   (decreasing per §2.2.6) without explicit user
   authorisation. Whether to reject this MAY be a per-
   transaction policy.
5. **Cyclic dependency unbreakable by ordering**: A cycle in
   the dependency graph that the resolver cannot resolve by
   plan ordering.

The resolver MUST report which condition failed and which
packages or constraints were involved.

## Optional dependencies

Optional dependencies (§4.1) MUST NOT be included in the
plan automatically. The resolver MAY surface them to the
user as suggestions but MUST NOT install them without
explicit instruction.

A package whose optional dependencies are not installed
MUST function correctly with reduced capability. A package
that does not function without an "optional" dependency has
mis-categorised that dependency: it is a required
dependency, not optional.

## Removal cascades

Removing a package whose other installed packages depend on
it would leave the system in an inconsistent state. A
removal operation MUST therefore either:

- Cascade: remove the dependent packages too (with explicit
  user authorisation), or
- Refuse: reject the removal and report the dependents that
  block it.

The choice between cascade and refuse MAY be a per-
transaction policy.

## Determinism

A conformant resolver MUST produce identical plans for
identical inputs. Given the same target set, installed set,
and available set, the resulting plan (or rejection)
MUST be deterministic.

This guarantees that "dry-run" output matches the actual
plan that would be applied if the operation proceeded.

## Bounded resolver work

A resolver MUST bound its work to prevent denial-of-
service via pathological dependency graphs. A consumer
MUST either:

- Implement an algorithm whose worst-case complexity is
  polynomial in the size of the available set and the
  target set, OR
- Apply an explicit step / runtime cap that terminates
  resolution with a clear error when exceeded.

The default cap MUST be reachable: the resolver MUST NOT
silently spin for unbounded time on a malicious input.
The exact cap is implementation-defined; values
producing tens-of-seconds latency on commodity hardware
for typical transactions are reasonable defaults.

> [!INFORMATIVE]
> Cyclic-dependency detection (§4.2.5(5)) requires the
> resolver to operate on the post-`provides`-resolution
> graph. The resolver MUST first substitute `provides`
> entries for the dependency-name they satisfy, then
> detect cycles in the resulting graph. Cycles in the
> raw `(name, depends-on)` graph that disappear after
> `provides` resolution are NOT errors.

## Resolution and the index

The resolver SHOULD perform satisfaction checks and
candidate selection using only data present in the
repository index (§6.2). Fetching the actual `.peipkg`
files SHOULD be deferred until after the plan is computed
and the user (or calling tool) has confirmed the operation.

> [!INFORMATIVE]
> The repository index includes the resolution-critical
> subset of each package's manifest (name, version,
> architecture, dependencies, conflicts, provides,
> replaces). A resolver does not need to download
> packages to compute the plan; this is the index's primary
> reason for existing.

## Atomicity

The plan MUST be applied atomically: either all operations
in the plan succeed, or none of them visibly take effect.
If any operation fails, the package manager MUST roll back
to the pre-resolution state.

The atomicity mechanism is specified in §7.4.

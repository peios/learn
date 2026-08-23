---
title: Cross-Repository Guards
description: The two relations that let one repository act on another's packages, and the gates on both.
---

Two relations let one repository act on another's packages, and both are
gated.

## Foreign replaces

A `replaces` declared by a lower-priority repository, targeting a
package originally installed from a higher-priority one, raises an
authorization. The operator confirms it specifically; a general `--yes`
does not satisfy it, and the authorising act is audited.

> [!NOTE]
> Without the gate, a custom repository silently replacing an
> official-repository package is a routine `upgrade` away. The
> confirmation is what stops an escalation happening as a side effect of
> an operation the operator thought was maintenance.

## Foreign conflicts

A `conflicts` declared by a lower-priority repository, which would cause
a higher-priority package to be removed as a cascade, is the mirror
image: a denial-of-availability rather than an escalation.

peipkg resolves a conflict by rejecting the plan outright rather than by
cascading removals, so the situation the guard describes does not arise:
the low-trust package simply fails to install, and the high-trust one
stays where it is.

## A low-trust provider filling a role

When the candidate that satisfies a dependency does so through
`provides` from a lower-priority repository, while a higher-priority
repository holds a name-matching package whose constraint check failed,
peipkg raises an authorization and requires explicit confirmation. This
is the same shape as the foreign-`replaces` guard: a less-trusted
package taking over a name a more-trusted one was expected to fill.

The check runs when resolving a dependency. It does not run for a
package the operator named directly, where it cannot fire in practice
because a directly named goal carries no constraint for the
higher-priority candidate to fail.

## Origin that no longer resolves

Each of these guards compares the priority of the repository a package
came from against the priority of the repository acting on it. A package
whose originating repository has since been removed has no configured
priority to compare, and peipkg skips the comparison — and with it the
guard — rather than treating the unknown origin as maximally trusted.

The consequence is worth stating plainly: for packages left behind by a
removed repository, the two gates above do not fire.

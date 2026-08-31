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
whose originating repository has since been removed — an **orphan** — has
no configured priority to compare, so it carries a priority below every
configurable value instead. Every guard that compares priorities
therefore treats an orphan as at least as trusted as anything still
configured, with no special case of its own.

That direction is the only safe one. Skipping the comparison, which is
what an unset priority produced, meant a newly added low-trust
repository could declare `replaces` against an orphaned ex-official
package and take it over with no confirmation — so removing a
repository *lowered* the protection on the packages it left behind.
Removing a repository because its keys were stolen is exactly when that
must not happen.

An orphan is not the same as a package with no origin. A raw local-file
install never had a repository to lose, and is not treated as maximally
trusted.

## Orphaned packages

`list` marks an orphan and names the repository that is gone; `info`
says so in the origin line. Neither is refreshed, and no trust state
stands behind either any longer.

An upgrade of an orphan is refused unless a configured repository now
serves a candidate under its own name. A *named* upgrade errors — the
alternative is reporting success having done nothing, since an unclaimed
orphan produces no upgrade operation at all. An every-package upgrade
warns per orphan and carries on, because one orphan must not stop the
rest of the system moving.

A `replaces` from another package can still move an orphan aside. That
is a takeover rather than an upgrade, and it is gated as an elevated
action by the rule above.

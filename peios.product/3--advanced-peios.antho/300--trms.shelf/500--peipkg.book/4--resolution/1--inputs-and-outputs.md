---
title: Inputs and Outputs
description: Turning "install this" into an ordered plan, entirely from index data before anything is fetched — inputs, outputs and determinism.
---

Resolution is the step that turns "install this" into "do these things,
in this order". It runs entirely on index data, before anything is
fetched.

## Inputs

- The **goals**: the operations the operator asked for. Install a
  package, upgrade one, downgrade one, or remove one.
- The **installed set**: what is on the system now, from the package
  database, with each package's version, architecture, originating
  repository, and that repository's priority.
- The **available set**: every package in every configured repository's
  index, each annotated with the repository it came from and that
  repository's priority.

The resolver's working model is keyed by the pair **(name, root)**. The
same package name installed in two roots is two independent entries,
possibly at different versions.

## Outputs

Resolution produces either a **plan** or a **rejection**.

A plan is an ordered list of operations. It is partially ordered so that
for every install, everything it depends on is already installed or is
scheduled earlier; removals are ordered in reverse, so that a dependent
is removed before the thing it depended on.

Alongside the plan, resolution emits two other things:

- **Authorizations** — elevated actions the plan implies, each of which
  the operator confirms on its own terms before the plan is applied.
  A downgrade, a foreign `replaces`, a low-trust provider filling a
  role.
- **Notices** — informational statements that never block. The
  substitution notice of §4.2 is one.

A rejection names which condition failed and which packages or
constraints were involved.

## Determinism

The resolver is a pure function of its inputs: the same goals, installed
set, and available set produce the same plan, every time. That is what
makes a dry run trustworthy — the plan shown is the plan that would be
applied.

Determinism holds with respect to the inputs *as given*, including the
order candidates appear in. Where the selection rules of §4.3 leave two
candidates genuinely tied, the one enumerated first wins, so a
re-sorted index can change the outcome.

## Index-only

Resolution never downloads a package. Satisfaction checks and candidate
selection use only what the index carries, which is why the index
carries a package's relationships at all. Fetching is deferred until
after the plan is computed and confirmed.

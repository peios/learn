---
title: What a TRM Is
description: What a technical reference manual is, why each component
  gets one book, where its authority comes from, and what belongs in one.
---

A **technical reference manual** (TRM) is an exhaustive descriptive
reference for one component: what it does, how it behaves at every
edge, and what happens when it fails.

The hardware analogy is deliberate. If the specification books are the
architecture reference manual, a TRM is the per-implementation technical
reference manual that sits beside them — the document that says what
one particular thing actually does, given that the architecture says
what any conforming thing must do.

## One book per component

A TRM covers one component, where the boundary is drawn by what ships
and is maintained together rather than by subject matter. Several
subsystems that live in one codebase and version together are chapters
of one manual, not manuals of their own.

## Its authority comes from the software

This is the property that governs everything else in this chapter. A
specification is authoritative over its implementations: where the two
disagree, the implementation has a defect. A TRM is the reverse. Where a
manual and the software disagree, the software is right and the manual
is stale.

A TRM therefore makes no stability commitment. Nothing in one is a
promise about a future version, and a reader who needs a promise needs a
specification instead.

## What belongs in one

Everything about the component that is true and not documented
elsewhere: its architecture, its state, how it uses its configuration,
its algorithms where they are its own, its failure modes, its on-disk
artifacts, and the reasoning behind its design decisions.

A manual SHOULD carry rationale generously. It is the only document in
the corpus with room for it, and a component's design decisions are
otherwise recorded only in the history of the work that produced them.

## What does not belong

Anything a third party must reproduce to interoperate. That is
a contract, and a contract belongs in a specification (§1.2). A manual
cites it (§4.6) rather than restating it.

Registry keys and values belong to regman, and events and their fields
to evman. A manual links to their pages rather than tabulating them
(§6.2).

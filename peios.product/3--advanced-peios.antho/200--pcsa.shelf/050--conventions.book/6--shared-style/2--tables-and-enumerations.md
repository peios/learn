---
title: Tables and Enumerations
description: Every exhaustive table has exactly one home, subsets are labelled as subsets, and disagreeing copies are resolved rather than averaged.
---

## One canonical home

Every exhaustive table or enumeration lives in exactly **one** place.
Everywhere else that needs it gets a clearly framed subset and a
reference to the canonical one.

This applies across the whole corpus, not within a single book: a table
in a specification is not re-tabulated in a manual, and a manual's
configuration reference is not duplicated into task documentation.

## Subsets are labelled as subsets

A partial table MUST be framed as partial. A reader who cannot tell a
subset from the full set will treat the subset as exhaustive, which is
how a table that was correct becomes a document that is wrong.

## Disagreeing copies are never averaged

Where two copies of a table disagree, the resolution is to check the
source — the implementation, or the specification that defines it — and
then to delete one of the copies. Splitting the difference produces a
third value that matches nothing.

## Layout tables

A table describing a binary layout is normative in a specification
(§3.3) and descriptive in a manual, and in both cases gives fields in
declaration order.

## Formatting

A table row MUST NOT contain an unescaped `|`. A pipe inside a cell —
common when documenting bitwise expressions — silently eats a column,
and the resulting table renders as though it always had one fewer.

A table SHOULD have a header row with a meaningful label per column.
`Field | Type | Description` beats three unlabelled columns.

Very wide tables SHOULD be broken up or transposed. A table that needs
horizontal scrolling is a table nobody reads the right-hand end of.

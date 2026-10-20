---
title: Tables and Enumerations
description: Why every exhaustive table has exactly one home, how subsets
  are labeled, how disagreeing copies are resolved, and the formatting
  rules tables need beyond Core Style.
---

A table that exists in two places will eventually disagree with itself.
The rules in this article keep each exhaustive table in one place and
make every other copy visibly partial.

## One canonical home

Every exhaustive table or enumeration lives in exactly one place.
Everywhere else that needs it gets a clearly framed subset and a
reference to the canonical one.

This applies across the whole corpus, not within a single book: a table
in a specification is not re-tabulated in a manual.

It also applies across the forms of Peios documentation. Registry
configuration is documented by regman, which owns it, and events by
evman. A technical reference manual does not have a configuration
reference of its own. It links to the regman and evman pages rather than
tabulating keys, values, events, or fields (see
[regman and evman](~psc/regman-and-evman)).

## Subsets are labeled as subsets

A partial table MUST be framed as partial. A reader who cannot tell a
subset from the full set will treat the subset as exhaustive, which is
how a table that was correct becomes a document that is wrong.

## Disagreeing copies are never averaged

Where two copies of a table disagree, the resolution is to check the
source (the implementation, or the specification that defines it) and
then to delete one of the copies. Splitting the difference produces a
third value that matches nothing.

## Layout tables

A table describing a binary layout is normative in a specification
(§3.3) and descriptive in a manual, and in both cases gives fields in
declaration order.

## Formatting

[Core Style](~psc/core-style) covers header rows, empty cells, and
cell length. Tables in this corpus add two rules.

A table row MUST NOT contain an unescaped `|`. A pipe inside a cell —
common when documenting bitwise expressions — silently eats a column,
and the resulting table renders as though it always had one fewer.

Very wide tables SHOULD be broken up or transposed. A table that needs
horizontal scrolling is a table nobody reads the right-hand end of.

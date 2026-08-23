---
title: Naming External Constants
description: Each document uses its own reader's vocabulary, divergences are tabulated once per book, and structures are distinguished from the constants that select them.
---

Much of what this corpus documents already has names — given by an
external standard, by a published header, or by both, spelled
differently. A reader arrives holding one of those names and expects to
find it.

## Each document uses its own reader's vocabulary

A **specification** is written for an implementer who has the external
standard and does not have this implementation's source. It uses the
**external standard's spelling**, exactly as that standard spells it.

A **technical reference manual** is written for someone reading
alongside the implementation. It uses the **implementation's spelling**,
exactly as the header declares it.

Neither adopts the other's vocabulary. A specification that named
private headers would be documenting something its reader cannot see,
and a manual that named only the standard would not match the code in
front of the reader.

## Divergences are recorded once per book

Where the two vocabularies disagree, the disagreement is stated **once**
— in a table, in an appendix — and not repeated at every use. Inline
double-naming makes prose unreadable to both audiences at once.

The table gives both spellings and nothing else. It is a lookup, not an
explanation.

## Where a standard names a structure and its constant separately

Many standards give one name to a structure and another to the constant
that selects it: a record type and the numeric tag identifying that
record. A reader may arrive with either — one from a declaration, the
other from a hex dump — so a table that gives a value MUST name the
constant that carries it, not only the structure it selects.

Naming the structure in a column headed with the constant's value is the
common form of this mistake. It reads correctly and is unfindable by
half the people who need it.

## The test

For any name a reader could plausibly arrive with, searching the corpus
for that exact string finds something. A name that appears only as prose
— "the offset to the owner SID", where the standard calls the field
`OffsetOwner` — fails this test even though the surrounding text is
correct.

Correct and unfindable is the failure this rule exists to prevent.
Reference material is read by search.

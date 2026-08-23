---
title: Proposals
description: A TRM for software that does not exist yet — why the class exists, how it says so, and how it graduates in place once the software does.
---

A **technical reference manual proposal** is a TRM for a component that
does not exist yet.

It is written exactly as a TRM is written — indicative mood, no
normative keywords, exhaustive — and it describes software that has not
been built.

## Why the class exists

A design that has been written out at reference-manual depth is a design
whose gaps are visible. Every field, limit, and interaction has to be
decided in order to be described, and describing it is how the
contradictions surface.

## Saying what it is

A proposal MUST identify itself as one. It SHOULD do so in two places:
in its description, and in an opening article stating plainly that a
manual's authority comes from the software (§4.1) and that this one has
none of that yet — so a surprising statement in it is a design decision
that has not survived contact with an implementation.

The document class carries that warning by itself, which is why no
banner on every page is needed.

## It graduates in place

A proposal sits alongside the finished manuals and **MUST NOT be moved**
when the software lands. Moving it breaks every inbound link.
Graduating consists of correcting it against the implementation and
dropping the word "proposal".

## Reviewing one

A proposal cannot be verified against code, so review is internal
composition instead: for each field, rule, limit, and configured value,
find every other place the document constrains it, and compose them by
hand.

The failure to look for is **two rules that are individually right and
jointly wrong** — a default stated in one chapter and a validity
constraint stated in another, which together reject the default. The
related one is **two rules with no stated order**, where both can fire
on one input and the document never says which runs first.

Composing every pair of independently configured size limits on one data
path, at their default values, is worth doing every time. Two documents
in a row have carried a ceiling on one side larger than the ceiling on
the other, letting one party accept what the other cannot carry.

A proposal MAY still contribute a specification chapter, where the
component owes one. Publishing a contract with no implementation to keep
it honest is a real cost, and it is a decision to take deliberately
rather than by default.

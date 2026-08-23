---
title: Granularity
description: The article is the finest addressable unit, why the clause-level scheme was retired, and how to write an article worth citing.
---

The finest addressable unit in this corpus is the **article** — the
`§N.M` form of §5.1.

There is no addressing below it. Headings within an article are not
numbered, and there is no scheme for citing an individual normative
statement.

## Why not

An earlier corpus defined one: clauses numbered implicitly by counting
normative statements within the deepest enclosing heading, cited as
`§3.2.1(4)`, with a validation rule for checking that a clause number
still resolved.

It was specified in detail and never adopted. Across thirteen documents
it was used eighteen times, and never once in the current corpus. What
it cost was real: every editorial change to an article renumbered the
clauses after it, so every citation into that article had to be checked
against a count that nothing computed.

Article-level citation has proved sufficient in practice. An article is
small enough to be a useful target and stable enough to be worth citing.

## Writing for citability

Because the article is the unit, an author SHOULD size articles so that
one is a sensible thing to point at. An article covering one rule is
easy to cite; an article covering nine unrelated rules forces every
citation to be approximate.

Where a single statement genuinely needs to be picked out, a citation
MAY name it in prose alongside the article reference:

```markdown
the duplicate-key rule of §5.9
```

## Reading an old citation

A `(N)` clause suffix in older material, or in a code comment predating
this corpus, refers to the retired scheme. It SHOULD be resolved to an
article reference when the surrounding text is next touched.

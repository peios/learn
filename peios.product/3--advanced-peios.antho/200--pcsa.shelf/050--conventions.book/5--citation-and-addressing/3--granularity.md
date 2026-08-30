---
title: Granularity
description: The article is the unit a § reference addresses; a named citation reaches one statement inside it. Why the clause-numbering scheme was retired, and why naming does not repeat its mistake.
---

The finest unit a `§` reference addresses is the **article** — the
`§N.M` form of §5.1. Headings within an article are not numbered, and
there is no `§` form that reaches inside one.

For prose that is the right size. A reader following a reference wants
the surrounding argument, not one sentence stripped of it.

It is the wrong size for a **test**. A test verifies one statement, and
an article holds many, so "this test covers §5.9" cannot say which of
§5.9's statements remain unverified. For that there is a second scheme,
addressing a statement by **name**.

## Named citations

A document MAY anchor an individual statement with a name:

```markdown
A source MUST reject a relative identifier outside its declared
range. [*psi.rejects-out-of-range-relative-id]
```

which is then cited from outside the corpus — from a test, or a code
comment — by qualifying it with the book's short name:

```rust
// Verifies PGSS *psi.rejects-out-of-range-relative-id
```

An anchor is a **locator, not a delimiter**. It marks a place; it does
not record where the statement it names begins or ends, and nothing
computes that. A reader follows the name and reads.

Four rules, all enforced by the builder:

- A name MUST be unique within its book. Citations from outside are
  qualified by the book's short name, so book scope is enough.
- A name MUST be lowercase, in dot- or hyphen-separated segments,
  beginning and ending with an alphanumeric.
- Only a **book** may carry an anchor. A citation is addressed through
  its book, so an anchor anywhere else could never be cited.
- An anchor MUST NOT appear inside a code block or inline code, where
  it is shown rather than declared.

A retired name MUST NOT be reused for a different statement. Nothing can
detect the reuse, and every citation that already existed silently comes
to mean something else.

## Why not clause numbers

An earlier corpus defined a finer `§` form: clauses numbered implicitly
by counting normative statements within the deepest enclosing heading,
cited as `§3.2.1(4)`, with a validation rule for checking that a clause
number still resolved.

It was specified in detail and never adopted. Across thirteen documents
it was used eighteen times, and never once in the current corpus. What
it cost was real: every editorial change to an article renumbered the
clauses after it, so every citation into that article had to be checked
against a count that nothing computed.

**A name is not a count.** It is written once, it does not shift when a
statement is inserted above it, and a change that would break it —
deleting the statement — is exactly the change that ought to break it.
The failure that retired clause numbering does not reach the named form,
which is why the two can coexist.

## Why a name and not an extent

A name identifies a statement; it does not describe one. Naming a
statement `copy-up.preserves-ownership` says which statement is meant,
not what it says, and the name does not grow when the statement gains an
exception. This is the same division as §5.2's: the reference is the
durable part, and the prose around it may drift.

An author MAY be tempted to mark where a statement *ends* as well as
where it is. The corpus does not offer that, deliberately. A name is
arbitrary, so nobody disputes it and nobody revises it; an extent
appears to have a correct answer, so it invites both, and every revision
of one buys nothing for the test or the code comment that cites it.
Statements also overlap and nest in prose — a rule and its exception —
in ways no bracketing scheme resolves cleanly.

## Writing for citability

Because the article is the unit a `§` reference reaches, an author
SHOULD size articles so that one is a sensible thing to point at. An
article covering one rule is easy to cite; an article covering nine
unrelated rules forces every citation to be approximate.

The same applies one level down. Where a paragraph holds several
statements that need separate names, an author SHOULD split the
paragraph rather than crowd it, since a paragraph is also the unit of
context a tool can report around an anchor.

Where a single statement needs picking out and no anchor exists, a
citation MAY name it in prose alongside the article reference:

```markdown
the duplicate-key rule of §5.9
```

## Reading an old citation

A `(N)` clause suffix in older material, or in a code comment predating
this corpus, refers to the retired scheme. It SHOULD be resolved to an
article reference, or to a named citation, when the surrounding text is
next touched.

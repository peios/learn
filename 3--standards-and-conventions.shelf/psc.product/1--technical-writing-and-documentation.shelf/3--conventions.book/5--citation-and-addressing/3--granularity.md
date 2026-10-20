---
title: Granularity
description: Why the article is the unit a § reference addresses, how a
  named citation reaches one statement inside it, and why clause
  numbering and statement extents are not used.
---

The finest unit a `§` reference addresses is the article, in the `§N.M`
form of §5.1. Headings within an article are not numbered, and there is
no `§` form that reaches inside one.

For prose that is the right size. A reader following a reference wants
the surrounding argument, not one sentence stripped of it.

It is the wrong size for a test. A test verifies one statement, and an
article holds many, so "this test covers §5.9" cannot say which of
§5.9's statements remain unverified. For that there is a second scheme,
addressing a statement by name.

## Named citations

A document MAY anchor an individual statement with a name:

```markdown
A source MUST reject a relative identifier outside its declared
range. [*psi.rejects-out-of-range-relative-id]
```

A test or a code comment outside the corpus then cites the name by
qualifying it with the book's short name:

```rust
// Verifies PGSS *psi.rejects-out-of-range-relative-id
```

An anchor is a locator, not a delimiter. It marks a place; it does not
record where the statement it names begins or ends, and nothing computes
that. A reader follows the name and reads.

The builder enforces four rules:

- A name MUST be unique within its book. Citations from outside are
  qualified by the book's short name, so book scope is enough.
- A name MUST be lowercase, in dot- or hyphen-separated segments,
  beginning and ending with an alphanumeric.
- An anchor MUST appear only in a book. A citation is addressed through
  its book, so an anchor anywhere else could never be cited.
- An anchor MUST NOT appear inside a code block or inline code, where
  it is shown rather than declared.

A retired name MUST NOT be reused for a different statement. Nothing can
detect the reuse, and every citation that already existed silently comes
to mean something else.

## Why not clause numbers

A finer `§` form is possible: clauses numbered implicitly by counting
normative statements within the deepest enclosing heading, cited as
`§3.2.1(4)`, with a validation rule for checking that a clause number
still resolves.

The corpus does not use it. Specified in detail for 13 Peios documents,
it was used 18 times. Its cost is real: every editorial change to an
article renumbers the clauses after it, so every citation into that
article has to be checked against a count that nothing computes.

A name is not a count. It is written once, it does not shift when a
statement is inserted before it, and the one change that breaks it —
deleting the statement — is exactly the change that ought to break it.
The failure that rules out clause numbering does not reach the named
form.

## Why a name and not an extent

A name identifies a statement; it does not describe one. Naming a
statement `copy-up.preserves-ownership` says which statement is meant,
not what it says, and the name does not grow when the statement gains an
exception. This is the same division as §5.2's: the reference is the
durable part, and the prose around it can drift.

An author might be tempted to mark where a statement ends as well as
where it is. The corpus does not offer that, deliberately. A name is
arbitrary, so nobody disputes it and nobody revises it. An extent
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

## Reading a clause citation

A `(N)` clause suffix, in a document or a code comment, refers to the
clause-numbering scheme the corpus does not use. It SHOULD be resolved
to an article reference, or to a named citation, when the surrounding
text is next touched.

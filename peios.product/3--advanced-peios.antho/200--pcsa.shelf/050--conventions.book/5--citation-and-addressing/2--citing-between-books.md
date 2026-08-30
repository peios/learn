---
title: Citing Between Books
description: Citing within a book, between books, by name, and into code — and why the reference, not the prose beside it, is the durable part.
---

## Within a book

A reference to another part of the same book omits the book name:

```markdown
The claim-path set is the union defined in §5.23.
```

## Between books

A reference to another book leads with that book's short name:

```markdown
A dependency is satisfied when the conditions of PSPU §5.21 hold.
```

The short name is the one declared in the book's own metadata — `PCDS`,
`PGSS`, `PSPK`, `PSPU`. A reference to a manual names the component:
`the peipkg TRM §7.4`.

## Referring to a whole book

```markdown
All identifiers in this chapter conform to PCDS.
```

## Prose and the reference are different things

A citation MAY be accompanied by prose naming what is at the other end:

```markdown
Sender authentication is performed by peer credential (§4.18).

The descriptor store article (§4.20) defines the retention rules.
```

The `§` reference is the durable part. The prose is a readability aid,
and it MAY drift across revisions without invalidating the reference —
which is also why prose alone is not a citation.

## In code and in commit messages

A code comment or a test referring to a documented rule SHOULD carry the
full citation, so that a search finds every site depending on it:

```c
/* Per PCDS §5.6: inherited ACEs precede explicit ones. */
```

Where the rule carries a named citation (§5.3), cite it by name
instead. It resolves to the statement rather than to the article
holding it, so a test says exactly what it verifies:

```rust
// Verifies PCDS *sd.inherited-aces-precede-explicit
```

> [!NOTE]
> This is the mechanism that makes a specification change tractable.
> When a rule moves, the citations are what tell you which code was
> relying on it. Prose references — "as the security descriptor spec
> says" — do not survive a grep.

---
title: Required Articles
description: The fixed opening and closing shape of a specification book and of each of its chapters, so a reader finds the same things in the same places.
---

A specification book and each of its chapters carry a fixed opening and
closing shape, so that a reader arriving at any chapter finds the same
things in the same places.

## Book level

A book MUST open with an introduction chapter containing:

| Article | Purpose |
|---|---|
| Scope | What the book covers, and what it does not — with each exclusion naming where the excluded thing *is* covered |
| Conventions | The book's RFC 2119 declaration and any notation specific to it (§3.3) |

## Chapter level

A chapter specifying a protocol or a format MUST open with:

| Article | Purpose |
|---|---|
| Scope and Roles | What the chapter specifies, and the roles that speak it (§3.2) |
| Terminology | Terms specific to the chapter |

and SHOULD close with an **Extension** article (§3.4) and a
**Conformance** article (§3.4), in that order, before any appendices.

A chapter defining a data structure rather than a protocol has no roles
and no conformance obligations of its own, and is exempt from both.

## Terminology delegates rather than repeats

A terminology article MUST define the terms the chapter introduces. A
term already defined elsewhere in the corpus MUST be delegated by
reference rather than redefined:

```markdown
Terms defined in §5.2 — package, manifest, payload, repository — are
used here with the same meaning and are not redefined.
```

> [!NOTE]
> A redefinition is a second definition, and two definitions of one term
> drift. Delegation costs the reader one click and costs the corpus
> nothing.

## Scope names its exclusions

A scope article's exclusion list MUST identify, for each excluded item,
which document covers it. An exclusion that names nothing tells a reader
the subject is out of scope without telling them where to go, which is
the least useful thing a scope article can do.

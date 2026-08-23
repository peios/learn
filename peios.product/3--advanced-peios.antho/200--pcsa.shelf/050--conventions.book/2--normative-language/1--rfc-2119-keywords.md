---
title: RFC 2119 Keywords
description: Uppercase MUST, SHOULD and MAY carry their RFC 2119 meanings; lowercase does not. Requirements are stated against a role, and SHOULD is a real choice.
---

A specification MUST declare its use of RFC 2119 keywords in its
conventions article (§3.1).

The following keywords, **when they appear in uppercase**, MUST be
interpreted as described in RFC 2119:

| Keyword | Meaning |
|---|---|
| MUST, MUST NOT | An absolute requirement or prohibition |
| SHALL, SHALL NOT | Synonyms for MUST and MUST NOT |
| SHOULD, SHOULD NOT | A requirement that may be set aside for a stated reason, the consequences of which are understood |
| MAY | Genuinely optional |
| REQUIRED, OPTIONAL | Synonyms for MUST and MAY, used adjectivally |

A specification MAY use a subset. Its conventions article MUST list
which keywords it uses.

## Lowercase is not a keyword

The same words in lowercase carry no normative weight. This is not a
loophole to be exploited: a lowercase "must" in a passage that reads as
a requirement is an editing defect, because the reader cannot tell
whether an obligation was intended.

An author writing a requirement MUST use the uppercase form. An author
writing description SHOULD reach for a verb that is not a keyword at
all — "is", "carries", "produces" — rather than relying on case to carry
the distinction.

## Requirements are stated against a role

A specification with more than one party MUST state each requirement
against the **role** rather than the program (§3.2). An obligation on a
consumer binds whatever process is acting as the consumer, and one
program may serve different roles on different interfaces.

## SHOULD means something

A SHOULD is not a soft MUST and not a decorative MAY. It marks a
requirement with a real exception, and a specification using one SHOULD
say what the exception is — either inline or in an adjacent note.

> [!NOTE]
> A SHOULD whose exception nobody can name is a MUST that the author
> was not confident enough to write. A SHOULD that nothing would ever
> satisfy is a MAY. Both are worth catching before publication, because
> an implementer reading either has to guess at an intent that was never
> formed.

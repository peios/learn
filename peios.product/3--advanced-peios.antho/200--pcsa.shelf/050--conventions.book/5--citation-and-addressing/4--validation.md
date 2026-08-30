---
title: Validation
description: A published book must contain no reference that fails to resolve — how to check, what the builder checks for you, and the two traps that survive a careless check.
---

## Every reference resolves

A published book MUST NOT contain a reference that does not resolve. A
reference to a chapter, article, or appendix that does not exist is an
error, not a cosmetic defect: it is indistinguishable, to a reader, from
a reference to something that was deleted.

## Checking

Because section numbers are positional (§5.1), any structural change
invalidates references — including references from *other* books, which
the author making the change is least likely to be looking at.

After a structural change, an author SHOULD:

1. Build the affected books and extract the actual chapter and article
   numbering from the rendered index.
2. Collect every `§` reference in the corpus.
3. Check each against that numbering.

Steps 1 to 3 are mechanical and worth automating. What is not mechanical
is whether a reference that still *resolves* still means what the citing
text implies. A reference to "the ordering rules of PSPU `§5.6`"
resolves happily after that article is rewritten to cover something
else.

> [!NOTE]
> The failure this catches is specific and common: an article count
> changes by one, every reference past that point is off by one, and
> every one of them still resolves — to the wrong article. Nothing
> reports an error, and the document is wrong in a way that reads as
> correct.

## Named citations are checked for you

Unlike `§` references, named citations (§5.3) are validated by the
builder: a duplicated name, a malformed one, or an anchor outside a book
fails the build. What the builder cannot check is the other direction —
whether a citation *from outside the corpus*, in a test or a code
comment, still names a statement that exists. Deleting an anchor is
therefore a deliberate act: grep the name across the repositories that
cite it before removing it.

## Two traps

**Line-wrapped references.** A citation split across a line break — the
book's short name at the end of one line and the `§` number at the start
of the next — is easy for a checker to miss and easy for an author to
introduce.

**Appendix forms.** A chapter appendix and a book appendix take
different forms (§5.1), and a reference using the wrong one resolves to
nothing — or worse, to something.

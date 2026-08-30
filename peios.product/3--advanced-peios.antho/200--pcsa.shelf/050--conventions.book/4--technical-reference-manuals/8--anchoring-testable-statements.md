---
title: Anchoring Testable Statements
description: A manual has no keywords to grep, so named citations are the only handle it can offer a test suite — where the anchor goes, what deserves one, and why the pass comes after the prose.
---

A specification's testable statements are already findable: they carry
RFC 2119 keywords, so `MUST` can be searched for and enumerated. A
manual has none, by the rule that defines the class (§4.2). Nothing in
its text distinguishes a behavioural claim from the prose around it.

A named citation (§5.3) is therefore not a convenience for a manual. It
is the only handle a manual can give a test suite, and the reason to
anchor one is usually that something outside the corpus needs to point
at it.

## Anchor after writing, not during

An author SHOULD write a manual, or a chapter of one, to completion
first, and add anchors in a separate pass afterwards.

Marking anchors while drafting interrupts the writing for a decision
that has nothing to do with the sentence being written. Choosing which
statements are testable is also a different kind of attention from
composing them: it reads the finished text as an implementer would,
looking for what could be observed, and that reading is easier when the
text is finished.

Where a component's manual is written before its tests exist — which is
usual — the anchoring pass is still worth running, because it is what
tells the test author where to start.

## Put the anchor on the heading

**By default an anchor goes on a section's heading, and a section gets
one.** A manual that is well structured already devotes a section to a
behaviour, so the section is the thing a test wants to cite, and the
heading is where the anchor belongs:

```markdown
### `ro` [*strata.ro-is-independent-of-filesystem]
```

An anchor on a heading rides the document's structure rather than one
sentence of prose. A sentence gets rewritten in the ordinary course of
keeping a manual true; a section is a more stable thing to have named,
and the anchor moves with it.

The exception is a section that states **several distinct behaviours**
— most often a table of error conditions, or a numbered list of rules
that each hold independently. There the section is the wrong unit: one
name for fourteen rules tells a test suite no more than the article
number did. Anchor those individually, in the table row or list item
that states each rule.

The test is not a count. It is whether a reader asking "which behaviour
does this name?" could get more than one answer.

## Choosing what to anchor

Anchor a statement that could be **observed**: a rule about what is
accepted or refused, a value, an ordering, a returned error, an
invariant that holds while the component runs.

Do not anchor rationale, comparison with prior art, an account of how
the source is organised where no behaviour follows from it, or a
restatement of something already anchored nearby. An anchor on prose
that no test could ever cite is worse than no anchor: it will be
counted as uncovered forever.

## Anchor where the rule is defined, once

A manual states its important rules more than once — in the article that
defines a rule, in a summary of consequences, in a table collecting
every error condition. Only the defining occurrence carries the anchor.

A second anchor on a restatement does not add coverage; it splits it.
Two names for one behaviour means two entries in a report, one test
between them, and no way for a reader to tell which name the other tests
were meant to cite.

The signals that a passage is a restatement rather than a definition are
usually explicit: it closes with a `§` reference to the article that
owns the rule, or it sits under a heading that disclaims authority. Where
a section says the articles above remain authoritative, it carries no
anchors at all.

The mirror of this also has to be checked. A summary left unanchored is
correct only if the rules it summarises are anchored where they are
defined — a table of error conditions whose rows appear nowhere else in
prose is a *definition*, however much it looks like a summary, and an
author SHOULD anchor its rows rather than leave the most testable
surface in the manual uncitable.

## One anchor is not one test

Coverage against a manual is *"does this citation have at least one
passing test"*. It is not a mapping.

In a specification a normative statement is often close to a single
testable behaviour. In a manual it frequently is not — an anchor is as
much a way of dividing a long descriptive document into pieces a test
suite can reason about as it is a single assertion, and several tests
may reasonably cite one name. An author SHOULD move toward one anchor
per behaviour where the prose allows it, and SHOULD NOT contort the
prose to achieve it.

> [!NOTE]
> The count of anchors in a manual is not a measure of its quality, and
> a chapter with few is not deficient. Descriptive chapters — an
> overview, a discussion of the model — legitimately carry almost none,
> because almost nothing in them is a claim a test could check.

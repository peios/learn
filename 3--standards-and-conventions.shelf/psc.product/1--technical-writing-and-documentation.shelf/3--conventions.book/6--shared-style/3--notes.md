---
title: Notes
description: What a note carries that the surrounding text cannot, namely
  the reasoning behind a rule, what a note must not be used for, and how
  often to use one.
---

A note carries what the surrounding text cannot: why the rule is the way
it is, what it defends against, and what was tried instead. It is
written as a note callout:

```markdown
> [!NOTE]
> Text.
```

In a specification a note is informative and is bound by §2.2. In a
manual, where nothing is normative, a note is a change of register
rather than of authority.

This is a wider job than [Core Style](~psc/core-style) gives a note, which is an
occasional aside. The departure is deliberate (§1.1): rationale is what
keeps a rule from being removed or misread in a later revision, and the
callout keeps it visibly separate from the rule itself. Core Style's
other admonition rules still apply, including never placing two in a
row.

## What a good note does

A good note does at least one of three things:

- **Names the failure the rule prevents.** Concretely, with the
  mechanism. "Without this, an attacker who controls a cache edge
  replays an older signed index and the consumer never notices" is worth
  10 lines of abstract rationale.
- **Records the alternative that was rejected, and why.** The next
  person to look at the design will otherwise propose it again.
- **Flags the counter-intuitive.** Where a reader's first instinct is
  wrong, a note is where to say so.

## What a note is not

A note is never any of these:

- A restatement, in different words, of the rule it accompanies
- A place to hide a requirement (§2.2)
- An apology for a design

## Density

Roughly one note per two or three articles is what has worked. A book
with a note under every heading has diluted the marker to the point
where readers skip them, which wastes the ones that matter.

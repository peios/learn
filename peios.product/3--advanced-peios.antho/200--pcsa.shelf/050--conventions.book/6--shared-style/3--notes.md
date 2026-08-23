---
title: Notes
description: What a note carries that the surrounding text cannot — the reasoning behind a rule — and what a note must not be used for.
---

A note carries what the surrounding text cannot: why the rule is the way
it is, what it defends against, what was tried instead.

```markdown
> [!NOTE]
> Text.
```

In a specification a note is informative and is bound by §2.2. In a
manual, where nothing is normative, a note is a change of register
rather than of authority.

## What a good note does

- **Names the failure the rule prevents.** Concretely, with the
  mechanism. "Without this, an attacker who controls a cache edge
  replays an older signed index and the consumer never notices" is worth
  ten lines of abstract rationale.
- **Records the alternative that was rejected**, and why. The next
  person to look at the design will otherwise propose it again.
- **Flags the counter-intuitive.** Where a reader's first instinct is
  wrong, a note is where to say so.

## What a note is not

- A restatement of the rule above it in different words.
- A place to hide a requirement (§2.2).
- An apology for a design.

## Density

Roughly one note per two or three articles is what has worked. A book
with a note under every heading has diluted the marker to the point
where readers skip them, which wastes the ones that matter.

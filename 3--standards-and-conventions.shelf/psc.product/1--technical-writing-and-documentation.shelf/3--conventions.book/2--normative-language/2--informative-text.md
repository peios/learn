---
title: Informative Text
description: Why everything in a specification is normative unless marked
  otherwise, how to mark informative text, what it must not contain, and
  what it is for.
---

All text in a specification is normative unless it is explicitly marked
otherwise. Informative text is the exception, and it is marked so that a
reader never has to guess which kind of statement they are reading.

## Marking

Informative text MUST be marked, using a note callout:

```markdown
> [!NOTE]
> This paragraph gives context and defines no behavior.
```

An inline aside introduced by "For example" or "Note:" is also
informative.

[Core Style](~psc/core-style) treats a note as an occasional aside. In a specification the
note callout also marks text as informative and carries the reasoning
behind a rule, which is a deliberate departure from Core Style (§1.1).

## Limits on informative text

Informative text MUST NOT contain an RFC 2119 keyword used in its
normative sense. Where a note needs to refer to required behavior, it
MUST cite the normative statement that defines it rather than restating
it.

> [!NOTE]
> The restriction exists because a requirement stated twice is a
> requirement that can drift. When a note paraphrases a rule and the
> rule later changes, the note becomes a second, contradictory
> specification that a reader has no way to rank against the first.

## What informative text is for

Rationale, worked examples, the attack a rule defends against, and the
alternative that was considered and rejected.

A specification SHOULD carry that material rather than omit it. A rule
whose reason is unrecorded is a rule that a later revision will remove
as redundant, or preserve for the wrong reason — and a wrong reason is
what the revision after that will reason from.

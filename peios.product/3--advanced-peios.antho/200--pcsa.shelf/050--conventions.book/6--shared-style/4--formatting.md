---
title: Formatting
description: The mechanical conventions — line length, frontmatter, headings, code identifiers, text hygiene and spelling.
---

Mechanical conventions. None of these affects meaning; all of them
affect whether a diff is readable.

## Line length

Prose SHOULD wrap at 78 columns. Tables, code blocks, and link-heavy
lines are exempt — breaking those hurts more than it helps.

The reason is diffs. A paragraph on one long line produces a
whole-paragraph diff for a one-word change, which makes review of a
large document impractical.

## Frontmatter

Every article carries YAML frontmatter with a `title` and a
`description`:

```yaml
---
title: Freshness and Rollback Protection
description: An index that verifies is not necessarily current — monotonic
  versions, staleness limits, and the defences against rollback and freeze.
---
```

Titles are in title case, and name the subject rather than describing
it. "Freshness and Rollback Protection", not "How freshness works".

The description is one sentence saying what the article covers. It is
what a reader sees in a search result, so it does the work the title
deliberately does not: where the title names the subject, the
description says what is in there. It SHOULD name the specific things —
"monotonic versions, staleness limits" beats "the freshness rules" —
because a corpus this size has many articles called Overview, Structure
and Conventions, and the description is what tells them apart.

Do not restate the title. `title: Persistence` with
`description: How persistence works` has spent a line and told the
reader nothing.

Books were written without descriptions for a time, and the omission
was invisible until search made it obvious. The site build takes
`--strict`, which fails on any article missing one; run it that way.

## Headings

Articles use `##` for their top-level headings. An article does not
repeat its own title as a heading — the renderer supplies it.

Heading text is short and specific. Because headings are not addressable
(§5.3), they are navigation rather than citation targets, and they
SHOULD read as scannable labels.

## Code and identifiers

Identifiers, paths, field names, and literal values are in backticks.
Fenced blocks carry a language tag where one applies.

Code spans are not translated: a field named `size_installed` is written
that way in prose, not as "size installed".

## Text hygiene

Straight quotes and apostrophes rather than typographic ones; a regular
hyphen rather than a non-breaking one; a normal space rather than a
non-breaking space; and no zero-width characters. Each of those renders
identically and greps differently, which is the worst combination.

An em dash is written as `—`, spaced as the surrounding prose requires.

## Spelling

British English, except in identifiers, code, and the names of external
standards, which are reproduced exactly as their source spells them.

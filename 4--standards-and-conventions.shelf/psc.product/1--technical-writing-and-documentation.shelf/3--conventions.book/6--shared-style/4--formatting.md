---
title: Formatting
description: What specifications and technical reference manuals add to
  Core Style's formatting rules, covering frontmatter without a type,
  descriptions that name specifics, headings, the strict build, and
  spelling.
---

[Core Style](~psc/core-style) sets the formatting rules every form of
Peios documentation shares, including line length, frontmatter titles,
heading levels and case, code formatting, and text hygiene. This article
records only what specifications and technical reference manuals add.

## Frontmatter

Every article carries YAML frontmatter with a `title` and a
`description`:

```yaml
---
title: Freshness and Rollback Protection
description: Why an index that verifies is not necessarily current, and
  the monotonic versions, staleness limits, and defenses against rollback
  and freeze that address it.
---
```

The description is one sentence, wrapped at 78 columns with each
continuation line indented by two spaces.

An article in a specification or a manual is an article in a book, so it
carries no `type:` field. Core Style's page types apply to topics, and
the document class (§1.2) does the job for a book.

The description SHOULD name the specific things. "Monotonic versions,
staleness limits" beats "the freshness rules," because a corpus this
size has many articles called Overview, Structure, and Conventions, and
the description is what tells them apart.

The site build takes `--strict`, which fails on any article missing a
description; run it that way.

## Headings

Because headings are not addressable (§5.3), they are navigation rather
than citation targets, and they SHOULD read as scannable labels.

## Spelling

US English, as Core Style sets out. Identifiers, code, and the names of
external standards are reproduced exactly as their source spells them.

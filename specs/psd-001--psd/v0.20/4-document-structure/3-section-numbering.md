---
title: Section Numbering
---

## Numbering scheme

The numbering scheme derives from the filesystem structure:

| Level | Source | Format |
|---|---|---|
| Chapter | Directory numeric prefix | `N` |
| Section | File numeric prefix within chapter | `N.M` |
| Subsection | `##` heading order within file | `N.M.K` |
| Sub-subsection | `###` heading order within parent `##` | `N.M.K.L` |
| (deeper) | Each heading level adds a dot-separated component | unlimited depth |

Chapter directories MUST use the format `N-name/` where `N` is a positive integer. Files within chapters MUST use the format `N-name.md` where `N` is a positive integer.

Chapter and section numbering MUST start at 1 within their parent. Numbers MUST be sequential -- gaps SHOULD NOT exist in finalized versions but MAY exist in drafts.

## Subsection numbering

Subsections are numbered by the sequential order of headings within a file, not by explicit numeric prefixes. The first `##` heading in a file is subsection 1, the second is subsection 2, and so on. Nested headings (`###`, `####`) restart numbering within their parent heading.

> [!INFORMATIVE]
> Example: in `3-security-descriptors/2-acls.md`:
>
> ```markdown
> ## Overview          ← §3.2.1
> ## ACE Ordering      ← §3.2.2
> ### By Type          ← §3.2.2.1
> ### By Position      ← §3.2.2.2
> ## Inheritance       ← §3.2.3
> ```
>
> The chapter number (3) comes from the directory prefix. The section number (2) comes from the file prefix. Subsection numbers come from heading order.

## Files without subsection headings

A section file with no `##` headings has no subsections. Content is addressed at the section level: `§3.2`, `§3.2(1)`.

## Stability

Section numbers are positional. Inserting a chapter shifts all subsequent chapter numbers. Inserting a file shifts subsequent section numbers within that chapter. Inserting a `##` heading shifts subsequent subsection numbers within that file.

Within a `final` version, the structure MUST NOT change. Section numbers are frozen on finalisation.

When a new version restructures content, the changelog (see §7.1) MUST document structural changes that affect numbering.

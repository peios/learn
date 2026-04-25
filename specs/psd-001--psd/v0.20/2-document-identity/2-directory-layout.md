---
title: Directory Layout
---

## Specification root

All specifications MUST reside under the `specs/` directory. Each specification MUST have its own directory named according to the `psd-NNN--name` convention defined in §2.1.

## Version directories

Within a specification directory, each version MUST have its own directory named `vMAJOR.MINOR` or `vMAJOR.MINOR.PATCH` matching the Peios software version (see §3.1).

Examples:

```
specs/psd-004--kacs/
  trail.toml
  v0.20/
    trail.toml
    1-introduction/
    2-sids/
    3-security-descriptors/
    ...
  v0.22/
    trail.toml
    1-introduction/
    2-sids/
    3-security-descriptors/
    ...
```

Each version directory is a complete, self-contained edition of the specification. Version directories MUST NOT contain references to files in other version directories.

## Chapter directories

Within a version directory, chapters MUST be organised as numbered directories using the format `N-name` where:

- `N` is a positive integer (no zero-padding required)
- `name` is a kebab-case slug describing the chapter

Chapters MUST be numbered sequentially starting at 1. Gaps in numbering SHOULD NOT exist in finalized versions but MAY exist in drafts to reserve space for future chapters.

Appendix chapters MUST be numbered contiguously after the last substantive chapter.

> [!INFORMATIVE]
> Example appendix naming: if a specification has 10 substantive chapters, the first appendix is `11-appendix-a/` and the second is `12-appendix-b/`.

## Section files

Within a chapter directory, sections MUST be markdown files using the format `N-name.md` where:

- `N` is a positive integer
- `name` is a kebab-case slug describing the section

Section files MUST be numbered sequentially starting at 1 within their chapter.

## Subsections

Subsections within a section file MUST use markdown headings. The heading hierarchy maps to the addressing scheme:

- `##` headings are subsections
- `###` headings are sub-subsections
- Deeper nesting follows the same pattern

There is no enforced depth limit.

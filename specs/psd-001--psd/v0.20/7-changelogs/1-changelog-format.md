---
title: Changelog Format
---

## Requirement

Each version directory except the first MUST contain a `CHANGES.md` file documenting what changed from the previous version of the same specification.

The first version of a specification MUST NOT have a `CHANGES.md` file.

## Format

The changelog MUST use the following structure:

```markdown
# PSD-004 (KACS): Changes in v0.22

## Summary

One-paragraph overview of why this version exists.

## Breaking Changes

- §10.1(3) removed — access check no longer considers X
- §4.3(5) changed — token lifetime now bounded by Y

## Additions

- New chapter: 15-audit-events
- §7.2(12) added — new privilege for Z

## Structural Changes

- Former chapter 8 is now chapter 9 (new chapter 8 inserted)
- All §8.x references from other specs must be updated to §9.x

## Clarifications

- §3.2.1(7) reworded for clarity (no semantic change)
```

## Rules

The heading MUST identify the PSD number, specification name, and version.

Breaking changes and additions MUST reference section and clause addresses using the new version's numbering.

Structural changes that shift section numbering MUST be called out explicitly. This aids cross-reference validation by identifying which external references need to be updated.

Clarifications MUST explicitly state "no semantic change" when the rewording does not alter the meaning of the normative statement.

Sections with no entries MAY be omitted from the changelog.

---
title: Scope
---

This specification defines the conventions for writing, numbering, versioning, and citing Peios Specification Documents (PSDs). It is the governing document for the Peios spec corpus.

A PSD is a formal specification that defines the normative behavior of a Peios subsystem, data type, protocol, or convention. PSDs are the authoritative source of truth for implementation. Tests and existing code may reveal behavior, but they are not the semantic authority -- where a PSD and an implementation disagree, the PSD is correct and the implementation has a bug.

This specification covers:

- PSD numbering -- assignment, format, and permanence of PSD identifiers
- Directory layout -- filesystem conventions for specs, versions, chapters, and sections
- Versioning -- SemVer synchronisation with Peios software releases, revision counting, lifecycle states, and version resolution
- Document structure -- chapter, section, and file organisation; required sections; frontmatter; section numbering
- Normative language -- RFC 2119 keywords, informative blocks, pseudocode conventions, clause numbering
- Citations -- the `§` addressing scheme, cross-references within and between specs, version resolution
- Changelogs -- format and rules for documenting changes between versions
- Dictionary integration -- term definitions and auto-linking

This specification does not cover:

- Trail (the static site generator) implementation details -- Trail renders PSDs but is specified separately
- Conformance tracking -- coverage matrices and conformance reports are implementation artifacts, not spec management
- Review workflow -- the process by which specs are reviewed and approved is a project convention, not a PSD concern

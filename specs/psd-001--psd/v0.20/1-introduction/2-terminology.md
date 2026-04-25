---
title: Terminology
---

- **PSD** (Peios Specification Document): A formally numbered specification in the Peios spec corpus. Each PSD has a permanent numeric identifier and one or more versioned editions.

- **PSD number**: A sequential positive integer permanently assigned to a specification. Format in prose: `PSD-NNN` (zero-padded to three digits). PSD numbers identify specifications, not versions.

- **Version**: A specific edition of a PSD, identified by a SemVer string synchronised with the Peios software release it ships with. Versions are sparse -- a PSD may jump from v0.22 to v0.56.1.

- **Revision**: The count of how many versions a PSD has had. Derived from the number of version directories. Not stored explicitly.

- **Chapter**: A top-level section of a PSD, corresponding to a numbered directory within the version directory. Example: `3-security-descriptors/` is chapter 3.

- **Section**: A file within a chapter directory. Example: `2-acls.md` within chapter 3 is section 3.2.

- **Subsection**: A markdown heading within a section file. `##` headings are subsections; `###` headings are sub-subsections. Depth is unlimited.

- **Clause**: A specific normative statement within a section or subsection. Clause numbers are positional -- derived by counting normative statements sequentially within the most specific section. Cited in parentheses: `(1)`, `(2)`.

- **Normative**: Text that defines required, prohibited, or permitted behavior. All text in a PSD is normative unless explicitly marked otherwise.

- **Informative**: Text that provides explanation, context, or examples but does not define behavior. Marked with `> [!INFORMATIVE]` block quotes or introduced with "For example" or "Note:".

- **Version resolution**: The rule by which a PSD reference without an explicit version is resolved: the highest version of the referenced PSD whose version number is less than or equal to the version of the referencing document.

- **Trail**: The Peios static site generator that renders PSDs. Trail is the primary publication tool but PSDs are designed to be readable and navigable without it.

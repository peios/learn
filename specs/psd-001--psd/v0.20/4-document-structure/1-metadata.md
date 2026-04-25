---
title: Metadata
---

## Specification-level metadata

Each specification MUST have a `trail.toml` file in its specification directory containing:

```toml
name = "KACS"
description = "Kernel Access Control Subsystem — tokens, security descriptors, access checks, and integrity controls."
```

- `name`: The short display name of the specification. MUST match the name component of the directory (case may differ).
- `description`: A one-line description of what the specification covers.

No other fields are required at the specification level.

## Version-level metadata

Each version MUST have a `trail.toml` file in its version directory containing:

```toml
status = "draft"
date = "2026-04-24"
```

- `status`: The lifecycle state. See §3.2 for valid values and transition rules.
- `date`: The date of the most recent change to this version, in `YYYY-MM-DD` format.

No other fields are required at the version level.

## File-level metadata

Every markdown file within a specification MUST have YAML frontmatter containing at minimum:

```yaml
---
title: Page Title
---
```

The `title` field is the display name of the section. No other frontmatter fields are required.

> [!INFORMATIVE]
> Trail uses the `title` field for navigation, page headers, and search indexing. The title does not need to match the filename -- `2-acls.md` may have `title: Access Control Lists`.

---
title: Dictionary Integration
---

## Dictionary files

Peios maintains a corpus-wide dictionary of defined terms in `dict/` at the learn site root. Each product or specification domain has its own dictionary file in TOML format.

A specification that introduces new terms SHOULD have a corresponding dictionary file at `dict/<name>.toml`.

## Term format

Dictionary entries MUST use the following TOML structure:

```toml
[[terms]]
term = "Security Identifier"
abbr = "SID"
aliases = ["SID"]
definition = "A variable-length binary value that uniquely identifies a principal."
category = "Identity"
product = "kacs"
etymology = "From Windows SIDs (MS-DTYP §2.4.2)"

[[terms.refs]]
label = "SID Format Specification"
path = "spec/kacs/v0.22/sids/format"
```

Required fields:

- `term`: The full display name of the term.
- `definition`: The definition text.
- `category`: A grouping category for related terms.

Optional fields:

- `abbr`: An abbreviation (e.g., "SID", "KACS").
- `aliases`: A list of alternative names for the term.
- `product`: Which product or specification this term belongs to.
- `etymology`: Historical source or origin of the term.
- `refs`: An array of references linking to specification sections.

## Auto-linking

The learn site configuration MUST enable automatic dictionary linking:

```toml
[dictionary]
auto_link = true
```

When auto-linking is enabled, Trail SHOULD automatically link occurrences of defined terms in rendered specification text to their dictionary entries.

## Relationship to terminology sections

Dictionary entries provide corpus-wide definitions for Trail to auto-link. Terminology sections within individual specifications (§4.2) provide specification-scoped definitions and may delegate to other specifications. The two mechanisms are complementary -- a term may appear in both a dictionary file and a terminology section.

---
title: Case Folding
description: Names are case-insensitive but case-preserving, implemented by storing both the written form and a folded one.
---

Key names and value names are case-insensitive but case-preserving. loregd
implements this by storing both forms: the name as written, and a folded
form alongside it in a `_folded` column.

The folded form is computed once, when the name is written, and it is the
folded column that appears in every `WHERE` clause and every primary key.
Lookups are therefore plain binary comparisons:

```sql
SELECT * FROM path_entries
WHERE parent_guid = ? AND child_name_folded = ?
```

This is why no custom SQLite collation is registered anywhere in loregd —
the case-insensitivity has already happened by the time SQLite sees the
query. The canonical name is what comes back in responses, so callers see
the case they originally supplied while storage compares the folded form.

Hive names are folded too, though not stored: routing a request to a hive
and rejecting duplicate hive declarations (§2.1) both compare folded
names.

Layer names are **not** folded. They are compared as binary, so layer
names are case-sensitive.

## How the folded form is computed

loregd derives the folded form from the Go standard library's
`unicode.ToLower`, with three corrections where lowercasing and simple
case folding disagree:

| Codepoint | Folds to | Why the correction |
|---|---|---|
| U+00B5 MICRO SIGN | U+03BC GREEK SMALL LETTER MU | Lowercasing leaves it unchanged. |
| U+017F LATIN SMALL LETTER LONG S | U+0073 LATIN SMALL LETTER S | Lowercasing leaves it unchanged. |
| U+0130 LATIN CAPITAL LETTER I WITH DOT ABOVE | unchanged | Its folding is a two-codepoint sequence, which simple folding does not produce. |

The standard library's case tables are **Unicode 15.0.0**.

> [!IMPORTANT]
> Lowercasing is not case folding, and the three corrections above do not
> close the gap. 219 codepoints fold to something other than their
> Unicode 16.0 simple case folding, and for 47 of those, case-insensitive
> matching fails outright: two spellings that name the same key do not
> reach the same folded form.
>
> Greek final sigma is the most reachable example. `ς` folds to itself,
> so a key stored as `Σ` is not found by a lookup for `ς`. The Cyrillic
> historic letters at U+1C80–U+1C88 and the Greek symbol variants
> `ϐ ϑ ϕ ϖ ϰ ϱ ϵ` behave the same way. Characters introduced in Unicode
> 16.0 — the Garay block among them — have no case mappings in the 15.0
> tables at all, so their case pairs never match.
>
> The Cherokee blocks fold in the opposite direction to the standard,
> across 172 codepoints. Matching inside a hive stays self-consistent,
> but the bytes written to the folded columns are not what another
> implementation folding the same names would produce.

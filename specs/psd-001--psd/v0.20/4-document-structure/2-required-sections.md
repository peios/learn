---
title: Required Sections
---

## Introduction chapter

Every PSD MUST have a `1-introduction/` chapter containing at minimum:

| Section | File | Purpose |
|---|---|---|
| Scope | `1-scope.md` | What the specification covers and does not cover. |
| Terminology | `2-terminology.md` | Defined terms, or delegation to terms defined in other PSDs. |
| Conventions | `3-conventions.md` | RFC 2119 declaration, pseudocode notation, byte order, string encoding, and other notational conventions. |
| Prior Art | `4-prior-art.md` | Parity mappings, reference material, and design influences. |

Additional introduction sections MAY be added after the required four.

### Scope

The scope section MUST list what the specification covers and what it does not cover. Items excluded from scope SHOULD identify which specification or subsystem covers them.

### Terminology

The terminology section MUST define terms specific to this specification. Terms already defined in another PSD MAY be delegated by reference rather than redefined:

```markdown
Terms defined in PSD-006 (LCS, RSI, hive, source, key, value,
layer) are used here with the same meaning and are not redefined.
```

### Conventions

The conventions section MUST declare conformance to PSD-001 and MUST declare the use of RFC 2119 normative keywords. It SHOULD document any notational conventions used in the specification, including:

- Pseudocode notation (see §5.3)
- Byte order (if the specification defines binary formats)
- String encoding (if the specification defines string handling)

### Prior art

The prior art section MUST document the design influences, reference material, and compatibility considerations for the specification. The content varies by specification:

- For specifications with a clear predecessor (e.g., Windows Security Model): parity mappings documenting what is faithful, what diverges, and what is omitted.
- For specifications based on external standards (e.g., RFCs, ISO standards): which standards, which parts adopted, which parts rejected.
- For novel specifications: design influences, alternative approaches considered, and rationale for the chosen design.

> [!INFORMATIVE]
> Existing Peios specifications use either `4-parity.md` or `4-compatibility.md` for this section. Both names are acceptable -- the requirement is for the content, not the filename. New specifications SHOULD use `4-prior-art.md` for consistency.

## Substantive chapters

Every PSD MUST have at least one substantive chapter beyond the introduction. The number and organisation of substantive chapters is at the author's discretion.

## Appendices

Appendix chapters MUST be numbered contiguously after the last substantive chapter and SHOULD use the naming convention `N-appendix-a/`, `N+1-appendix-b/`, etc.

## Reference tables

Specifications that define registry schemas, constant sets, configuration parameters, or other enumerable artifacts SHOULD include a reference appendix that consolidates all such items with back-references to the normative section where each is defined.

Each entry in a reference table SHOULD include at minimum the item identifier (key path, constant name, etc.) and a `§` citation to the section that defines its semantics. Additional columns (type, default value, description) are at the author's discretion.

> [!INFORMATIVE]
> Example: PSD-005 §11.4 consolidates all LCS self-configuration parameters with their types, defaults, valid ranges, and back-references to the sections that define their semantics. PSD-007 §14.1 consolidates all registry keys that peinit reads or writes. These tables serve as quick-reference indexes into the normative text.

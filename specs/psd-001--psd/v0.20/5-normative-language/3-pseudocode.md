---
title: Pseudocode Conventions
---

PSDs that include pseudocode MUST document their pseudocode conventions in the conventions section of the introduction chapter (§1.3).

The following conventions are established across existing Peios specifications and SHOULD be used by new specifications for consistency:

| Symbol | Meaning |
|---|---|
| `&` (parameter prefix) | In-out parameter -- the caller's value is read and may be modified |
| `\|` | Bitwise OR |
| `&` (in expressions) | Bitwise AND |
| `~` | Bitwise NOT |
| `\|=`, `&=` | Augmented assignment |
| `=` | Assignment |
| `==` | Equality comparison |
| `->` | Field access on a pointer or reference |
| `→` | Return type in function signatures |
| `//` | Single-line comment |

Pseudocode MUST be enclosed in fenced code blocks (triple backticks).

> [!INFORMATIVE]
> A specification MAY use additional pseudocode conventions (e.g., `and`, `or`, `not` for boolean operators; named error return codes). Any such extensions MUST be documented in the specification's conventions section.

## Type conventions

The following type conventions are established across existing specifications:

- All access masks are 32-bit unsigned integers unless otherwise stated.
- SID comparison is byte-for-byte equality of the binary encoding.
- GUID comparison is byte-for-byte equality of the 16-byte binary value.

A specification that relies on any of these conventions MUST state so explicitly rather than assuming the reader knows the convention.

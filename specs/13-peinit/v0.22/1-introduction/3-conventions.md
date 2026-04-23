---
title: Conventions
---

This specification uses the key words MUST, MUST NOT, SHALL, SHALL
NOT, SHOULD, SHOULD NOT, MAY, REQUIRED, and OPTIONAL as described
in RFC 2119.

> [!INFORMATIVE]
> "MUST" and "SHALL" indicate absolute requirements. "MUST NOT" and
> "SHALL NOT" indicate absolute prohibitions. "SHOULD" indicates a
> recommendation that may be departed from in particular
> circumstances with full understanding of the implications. "MAY"
> indicates a truly optional feature.

Pseudocode in this specification uses the following conventions:

- `&` as a parameter prefix denotes an in-out parameter (the
  caller's value is read and may be modified).
- `=` is assignment. `==` is equality comparison.
- `and`, `or`, `not` are boolean operators.
- `|` denotes bitwise OR. `&` in expressions denotes bitwise AND.
- `//` introduces a comment.
- `->` denotes field access on a structure.
- Functions return values via `return`. Error conditions return
  named error codes (e.g., `return ETIMEDOUT`).

Structure definitions use the following format:

```
ServiceDefinition {
    field_name:  type       // description
    field_name:  type?      // nullable (absent or not set)
    field_name:  type[]     // array
}
```

State machine transitions are written as:

```
From -> To [guard condition] / action
```

Registry paths use backslash as the path separator (e.g.,
`Machine\System\Services\`). This matches the LCS convention.

All timeout and interval values in the service definition schema
are in seconds unless explicitly stated otherwise.

JSON examples in the control interface sections represent the
exact wire format. Field names, types, and value formats are
normative. Enum values in JSON use snake_case (e.g., `"start"`,
`"admin"`, `"active"`, `"explicit_start"`, `"service_main"`).
Error codes in JSON use UPPER_SNAKE_CASE (e.g.,
`"ACCESS_DENIED"`). Enum values in structure definitions and
prose use PascalCase (e.g., Start, Admin, Active, ExplicitStart,
ServiceMain).

Section references within this specification use page titles
(e.g., "see the States and Transitions section").

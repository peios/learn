---
title: Version Constraints
description: How a relationship restricts which versions satisfy it — the operators, how they combine, and revision-relaxed operands.
---

A **version constraint** restricts which versions of a package satisfy a
relationship (§5.21).

## Operators

| Operator | Meaning |
|---|---|
| `=` | exactly equal |
| `>` | strictly greater than |
| `>=` | greater than or equal |
| `<` | strictly less than |
| `<=` | less than or equal |
| `!=` | not equal |

Comparison is by §5.6 in every case.

A bare version string with no operator is equivalent to `=`.

## Combining

Multiple expressions within one constraint string are separated by
commas and combined with logical AND. A version satisfies the constraint
if and only if it satisfies every expression.

```
libssl >= 3.0
libssl >= 3.0, < 4.0
nginx = 1.26.2-3
```

Whitespace around operators and commas is optional and MUST be ignored.

A constraint string MUST parse as one or more operator-and-version
expressions separated by commas. One that does not parse is invalid, and
an implementation MUST reject it.

## Revision-relaxed operands

A constraint's version operand MAY omit the `-<revision>` that a
complete version string otherwise requires.

An operand written without a revision — `>= 3.0` — constrains the epoch
and the upstream version only. A candidate satisfies it whenever its
epoch and upstream version satisfy the operator, whatever its revision.

An operand written in full constrains the revision as well.

> [!NOTE]
> This is what lets a dependency track a capability level rather than a
> packaging iteration. `libssl >= 3.0` is satisfied by `3.0-1` and by
> `3.0-7` alike; nothing about a repackaging of the same upstream
> release should change whether a dependency is met.

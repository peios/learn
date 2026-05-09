---
title: Version Comparison Reference
---

> [!INFORMATIVE]
> This appendix consolidates the version comparison
> algorithm defined normatively in §2.2. Where this
> appendix and §2.2 conflict, §2.2 wins.

## Top-level comparison

To compare two version strings A and B per §2.2.6:

1. Compare epochs (§2.2.2). If they differ, the higher
   epoch is greater.
2. If equal, compare upstream versions per the upstream
   comparison algorithm below.
3. If equal, compare peios revisions (§2.2.4) as
   integers. Higher revision is greater.
4. If all three are equal, the versions are equal.

## Upstream comparison algorithm

Defined normatively in §2.2.7.

### Tokenisation

A tokeniser walks the upstream string left to right and
emits a sequence of segments:

1. Non-alphanumeric characters (`.`, `+`, `-`, `~`) are
   separators and are not part of any segment.
2. A maximal run of digits forms a numeric segment.
3. A maximal run of letters forms an alphabetic segment.
4. A transition between digit and letter ends the
   current segment and begins a new one.

The tilde `~` marks any following segment as a
pre-release segment.

### Segment-pair comparison

| Left | Right | Result |
|---|---|---|
| numeric | numeric | compare as integers |
| alphabetic | alphabetic | compare by pre-release rank, then lexically |
| numeric | alphabetic (pre-release) | left is greater |
| numeric | alphabetic (not pre-release) | left is less |
| alphabetic (pre-release) | numeric | left is less |
| alphabetic (not pre-release) | numeric | left is greater |

Pre-release ranks are defined in appendix B.2 (§9.2).

### Implicit pre-release detection

A `-` separator preceding a non-pre-release alphabetic
segment within the upstream version is treated as if it
were a `~` separator: that alphabetic segment and all
subsequent segments in the same hyphen-delimited group
are marked as pre-release.

### End-of-string handling

When one segment sequence is shorter than the other, and
all common segments are equal:

| Next segment in longer | Result |
|---|---|
| numeric | shorter is less |
| alphabetic, pre-release | shorter is greater |
| alphabetic, not pre-release | shorter is less |

## Worked examples

| A | B | Result | Explanation |
|---|---|---|---|
| `1.0` | `1.0` | A = B | Identical |
| `1.0` | `2.0` | A < B | Numeric segment differs |
| `1.10` | `1.9` | A > B | Numeric, not lexical |
| `1.0` | `1.0.1` | A < B | Longer continues numerically |
| `1.0` | `1.0-rc.1` | A > B | Longer continues with pre-release |
| `1.0-rc.1` | `1.0-rc.2` | A < B | Numeric segment within pre-release |
| `1.0-alpha` | `1.0-beta` | A < B | Pre-release rank: alpha (1) < beta (2) |
| `1.0-rc` | `1.0-pre` | A > B | Pre-release rank: rc (4) > pre (3) |
| `1.0a1` | `1.0a2` | A < B | Numeric within concatenated pre-release |
| `1.0a1` | `1.0b1` | A < B | Pre-release rank: a (1) < b (2) |
| `1.0~rc1` | `1.0` | A < B | Tilde forces pre-release |
| `0:1.0` | `1:0.5` | A < B | Epoch dominates |
| `1.0-1` | `1.0-2` | A < B | Peios revision differs |
| `1.0-foo-1` | `1.0-1` | A > B | `foo` not pre-release; rank-5 alpha sorts after numeric |

## Constraint matching

A version V matches a constraint per §2.2.8 if and only
if V satisfies every operator-and-version expression in
the constraint, where:

| Operator | Match condition |
|---|---|
| `=` | V equals the operand |
| `>` | V is strictly greater than the operand |
| `>=` | V is greater than or equal to the operand |
| `<` | V is strictly less than the operand |
| `<=` | V is less than or equal to the operand |
| `!=` | V is not equal to the operand |

Multiple expressions in a single constraint are
AND-combined: V matches the constraint iff V matches
every expression.

## Implementation notes

> [!INFORMATIVE]
> The algorithm above is specified for clarity, not for
> efficiency. A correct implementation may use any
> internal representation that produces equivalent
> comparison results for all valid version pairs.
>
> A reference test vector set covering the worked examples
> and edge cases SHOULD be derived from this appendix and
> from §2.2 to verify implementation correctness across
> tooling. Such a vector set is not part of this
> specification but is recommended as a project artifact.

---
title: Pseudocode
description: Pseudocode in a specification is normative, and the corpus-wide conventions it should be written in.
---

A specification that includes pseudocode MUST document its conventions
in its conventions article (§3.1).

The conventions below are established across this corpus and SHOULD be
used, so that a reader moving between books does not have to relearn the
notation.

| Symbol | Meaning |
|---|---|
| `&` (parameter prefix) | In-out parameter — the caller's value is read and may be modified |
| `\|` | Bitwise OR |
| `&` (in an expression) | Bitwise AND |
| `~` | Bitwise NOT |
| `\|=`, `&=` | Augmented assignment |
| `=` | Assignment |
| `==` | Equality comparison |
| `->` | Field access through a pointer or reference |
| `→` | Return type in a signature |
| `//` | Single-line comment |

Pseudocode MUST appear in a fenced code block.

A specification MAY use further conventions — `and`, `or`, `not` for
boolean operators, or named error returns — and MUST document any it
uses.

## Pseudocode is normative

Pseudocode in a specification is a normative statement like any other,
and MUST be read as one. It is not an illustration of a rule stated
elsewhere; where it is meant as illustration, it belongs in a note
(§2.2).

> [!NOTE]
> This matters most for algorithms with an ordering that the prose does
> not make explicit. Two rules that can both fire on one input need a
> stated order, and pseudocode is often where that order actually lives.

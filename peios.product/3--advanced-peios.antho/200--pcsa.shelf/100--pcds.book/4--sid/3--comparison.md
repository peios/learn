---
title: Comparison
description: SID equality is an exact binary match — no case folding, no normalisation, no equivalence relation — and no total ordering is defined.
---

## Equality

Two SIDs are equal if and only if their binary representations are
byte-for-byte identical.

SID comparison MUST be performed on the binary encoding, not the
string form. There is no case sensitivity, normalisation, or
equivalence relation — equality is exact binary match.

## Ordering

This document does not define a total ordering for SIDs.
Specifications that require an ordered SID collection MUST define
their ordering convention explicitly.

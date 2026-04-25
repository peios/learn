---
title: Comparison
---

## Equality

Two GUIDs are equal if and only if their 16-byte binary
representations are identical.

GUID comparison MUST be performed on the binary representation,
not on string representations.

> [!INFORMATIVE]
> Byte-for-byte comparison of the binary form avoids case
> sensitivity and brace-presence issues that would arise from
> comparing string representations.

## Ordering

This specification does not define a total ordering for GUIDs.
Specifications that require an ordered GUID collection MUST define
their ordering convention explicitly.

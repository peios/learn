---
title: Comparison
---

## Equality

Two LUIDs are equal if and only if both their LowPart and HighPart
fields are identical.

## Ordering

This specification does not define a total ordering for LUIDs.
Although LUIDs are allocated monotonically within a boot session
(see §3.3), consumers MUST NOT rely on numeric ordering to infer
temporal relationships between LUIDs obtained from different
contexts.

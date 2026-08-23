---
title: Response Ordering
description: The queries behind enumerations carry no ORDER BY, so their order is not stable across calls — and what that means for the kernel.
---

The queries backing enumerations and lookups carry no `ORDER BY`, and a
`UNION ALL` across the two stores yields rows in whatever order SQLite
produces them. That order is not stable across calls.

The kernel walks enumeration results by dense index across repeated
calls, so an unstable order would make that walk duplicate or drop
entries. loregd therefore sorts every affected array into a canonical
order before encoding a response:

| Response | Sorted by |
|---|---|
| `RSI_LOOKUP` path entries | layer, then sequence |
| `RSI_ENUM_CHILDREN` children | folded child name |
| `RSI_ENUM_CHILDREN` per-child entries | layer, then sequence |
| `RSI_QUERY_VALUES` value entries | folded value name, then layer, then sequence |
| Key-metadata blocks, in any response | ascending GUID, compared bytewise |

This ordering is a wire-stability guarantee only. It has no bearing on
layer resolution, which is order-independent — the kernel selects a
maximum, not a first match.

## Arrays that are not sorted

Two arrays reach the wire in the order the query produced them:

- The **blanket-tombstone array** in an `RSI_QUERY_VALUES` response. It
  comes from an unordered `UNION ALL` like everything else, but is
  emitted unsorted.
- The **orphan-GUID array** in an `RSI_DELETE_LAYER` response. That
  operation walks every registered hive and concatenates their orphan
  sets, and the walk follows Go's randomised map iteration, so the array
  order differs between otherwise identical calls.

## Child display names

`RSI_ENUM_CHILDREN` groups rows by `child_name_folded` and emits one
child block per folded name, carrying a display name taken from the
`child_name` column.

Where two rows share a folded name but differ in stored case — `Foo` in
one store and `FOO` in the other, say — the display name emitted is
whichever row the unordered union yielded first. The *order* of children
is stable, because it is sorted on the folded name; the *case* of the name
reported for such a child is not.

---
title: Value Encoding
description: How every value in a result record is encoded — including why a GUID is a string — and why missing and null are the same value.
---

Every value in a result record is encoded as follows.

| Value | Encoding |
|---|---|
| Integer | MessagePack integer |
| Float | MessagePack `float64` |
| Timestamp | MessagePack integer, nanoseconds since the Unix epoch (§3.5) |
| String | MessagePack string |
| GUID | MessagePack string, PCDS canonical form |
| Binary | MessagePack `bin` |
| Boolean | MessagePack boolean |
| Array | MessagePack array |
| Absent or null | MessagePack nil |

A GUID is rendered as a string rather than as sixteen bytes because a
result record is read by people as often as by programs, and a raw GUID
in a terminal is unreadable. The canonical form is lowercase
`8-4-4-4-12` hexadecimal within braces, as PCDS defines it. A query
comparing against a GUID accepts either braced or unbraced input, and
compares case-insensitively (§3.19); a result always uses the canonical
form.

## Maps do not appear as values

An event payload is a MessagePack map, and result records are flat
(§3.22). A map in a stored payload is therefore a *container to be
flattened*, not a value to be emitted: its entries become top-level
keys of the record, joined by dots, and the map itself never appears.

Arrays are different. An array is emitted as an array value at its
flattened path, and a collector MUST NOT traverse into it. Maps nested
inside an array are preserved as that array's contents, unflattened and
unqueryable.

The asymmetry is deliberate. A map has keys, so its entries have names
that can be addressed, granted access to and indexed. An array has
positions, and a path like `hops.3.address` would mean something
different in every record — so an array is carried across whole and
treated as one value.

Binary values in a payload stay binary. A collector MUST NOT render
`bin` as a string, in either direction.

## Missing and null are the same value

A field absent from an event payload or from a metric's label set
encodes as nil, exactly as an explicitly null one does, and the two are
indistinguishable in a result record.

This is consistent throughout: they compare equal, they sort together,
and they group together (§3.20, §3.21). A collector MUST NOT distinguish
them anywhere in the query surface, and a client MUST NOT attempt to.

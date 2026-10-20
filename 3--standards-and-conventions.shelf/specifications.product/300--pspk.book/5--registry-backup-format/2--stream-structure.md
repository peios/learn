---
title: Stream Structure
description: Record framing, field encoding, ordering, and how the format is versioned and extended.
---

All multi-byte integers in this format are **little-endian**, in the
record framing and in every payload.

## Record framing

Every record begins with the same six-byte header.

| Offset | Size | Field |
|---|---|---|
| 0 | 2 | `record_type` |
| 2 | 4 | `record_len` |

`record_len` is the record's total size **including** this header, so
its minimum valid value is 6. The payload follows immediately.

A reader MUST validate `record_len >= 6` and MUST verify that the
record body can be read in full before acting on the record or
skipping it.

| Record | Code |
|---|---|
| `HEADER` | `0x01` |
| `LAYER` | `0x02` |
| `KEY` | `0x03` |
| `PATH_ENTRY` | `0x04` |
| `VALUE` | `0x05` |
| `BLANKET_TOMBSTONE` | `0x06` |
| `TRAILER` | `0xFF` |

## Field encoding

A **length-prefixed field** is a `u32` byte count followed by that many
bytes. Names — hive name, layer name, child name, value name — are
UTF-8. Three length-prefixed fields are **binary, not UTF-8**: a
`LAYER` record's owner SID, a `KEY` record's Security Descriptor, and a
`VALUE` record's data.

A **GUID** is 16 raw bytes. An all-zero GUID is nil and is valid only
where a record's definition says so.

## Ordering

```
HEADER                         exactly one, first
LAYER                          one per referenced layer, before any key data
  for each key, depth-first pre-order over the merged tree:
    KEY                        the key object
    PATH_ENTRY *               entries owned by this section
    VALUE *                    all layers' values for this key
    BLANKET_TOMBSTONE *        all layers' blankets for this key
TRAILER                        exactly one, last
```

The merged tree is the union of every layer's namespace. Depth-first
pre-order guarantees a key's parent precedes it.

The following are normative:

- `HEADER` MUST be the first record and MUST appear exactly once.
- Every `LAYER` record MUST precede all key data. A `LAYER` record
  after key data has begun is invalid.
- The **root** `KEY` record — the one whose GUID equals
  `HEADER.RootGUID` — MUST be the first `KEY` record in the stream, and
  MUST appear exactly once.
- Within a key's section, records MUST appear in the order
  `PATH_ENTRY`, then `VALUE`, then `BLANKET_TOMBSTONE`. A `PATH_ENTRY`
  after a `VALUE` or `BLANKET_TOMBSTONE` in the same section is
  invalid, as is a `VALUE` after a `BLANKET_TOMBSTONE`.
- No `PATH_ENTRY`, `VALUE` or `BLANKET_TOMBSTONE` may appear before the
  first `KEY` record.
- `TRAILER` MUST be the last record. Any record after it is invalid.

## Which section a path entry belongs to

A `PATH_ENTRY` naming a key belongs to **that key's** section: it is
one of the incoming entries for the key whose section it is in.

A HIDDEN entry has no key, so it cannot have a section of its own. It
belongs to the section of the key that is its **parent**, alongside
that key's other records. A HIDDEN entry masking a name where no key
exists in any layer is still valid — it expresses that a layer hides a
name, whatever else is or is not there.

A writer MUST NOT emit a GUID-bearing `PATH_ENTRY` in the **root**
key's section. On restore, the target key's existing name is
authoritative and such a record would be discarded. A reader MUST skip
one rather than treat it as an error.

A path entry's parent GUID may belong to a key that only has path
entries in a different layer. The merged-tree walk handles that; it is
not a special case.

## Versioning

`HEADER` carries two version numbers.

**`FormatVersion`** is the version the stream was written with.

**`MinReaderVersion`** is the oldest reader that can process the stream
correctly. A reader MUST reject a stream whose `MinReaderVersion`
exceeds its own supported version, before acting on any of it.

The current version is 21 in both fields, and readers support 21.

A writer that used only older features SHOULD set a lower
`MinReaderVersion`, so that older readers can restore the stream. A
writer MUST raise `MinReaderVersion` when a new record type is required
for a correct restore, so that an older reader refuses the stream
rather than restoring an incomplete one.

## Extension

Extension is by **new record types only**.

Unknown record types MAY appear anywhere between `HEADER` and
`TRAILER`. When `MinReaderVersion` permits, a reader MUST skip them,
and MUST treat them as inert: they do not begin or end a key section,
do not satisfy any required record, do not declare a layer, and do not
affect root mapping, sequence remapping or any validation rule. They
**do** count toward `TRAILER.RecordCount` and they **are** covered by
the checksum.

A record payload MUST be consumed **exactly**. Trailing bytes inside a
record of a known type are invalid, even though `record_len` would
accommodate them. A reader MUST NOT skip unrecognised trailing data
within a known record, and a writer MUST NOT add any.

This is deliberately the opposite of the RSI's request convention. A
stream is replayed into mutations long after it was written, and a
field silently ignored there is data silently lost.

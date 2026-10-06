---
title: "stratafs.file.copied-up"
description: "The record that StrataFS materialised an object into a writable stratum, successful or not."
---

- **Event type:** `stratafs.file.copied-up`
- **Defined in:** `stratafs.evman`
- **Tier:** standard
- **Gating:** none — every copy-up is recorded
- **Cardinality:** one record per occurrence

The record that StrataFS materialised an object into a writable stratum,
successful or not. Copy-up is how a layered mount turns a read-only object
into a writable one, so this is the record of a file coming into existence
in a place it did not previously exist.

The record is written through KACS, so its `emitter.class` is `kacs`.

**There is no subject in the payload, and that is not an omission.**
Copy-up preserves the source object's descriptor, so the resulting file
records nothing about who caused it to exist. The actor is identified by
the header instead: copy-up runs in the caller's own context, so
`emitter.token.guid` and `emitter.process.guid` are the caller's.

That identification is currently weaker than it looks. The header carries
GUIDs and nothing in the stream binds a GUID to a SID, an image or a
process name, so an operator reading these records can group them by actor
but cannot say who the actor was.

**`ENOTDIR` from a failed parent materialisation surfaces here**, in
`outcome.errno`, rather than as a refusal record. Searching
`stratafs.mutation.refused` for it finds nothing; the record exists under
this type with every field present.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.file.path-relative`](~peios/events/field-index/fields-object#object.file.path-relative) | `str.path` | required | The path of the object within its mount, `/`-prefixed. |
| [`source.stratum.index`](~peios/events/field-index/fields-source#source.stratum.index) | `uint` | required | Which stratum an object was read from, by index within the mount's stack. |
| [`source.stratum.path`](~peios/events/field-index/fields-source#source.stratum.path) | `str.path` | required | The filesystem path of the stratum an object was read from. |
| [`destination.stratum.index`](~peios/events/field-index/fields-destination#destination.stratum.index) | `uint` | required | Which stratum an object was written into, by index within the mount's stack. |
| [`destination.stratum.path`](~peios/events/field-index/fields-destination#destination.stratum.path) | `str.path` | required | The filesystem path of the stratum an object was written into. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

---
title: "stratafs.mutation.refused"
description: "The record that a mutation was refused because of how the mount is arranged, rather than because of an access check."
---

- **Event type:** `stratafs.mutation.refused`
- **Defined in:** `stratafs.evman`
- **Tier:** standard
- **Gating:** none — every arrangement refusal is recorded
- **Cardinality:** one record per occurrence

The record that a mutation was refused because of how the mount is
arranged, rather than because of an access check. Software writing where it
cannot, or an arrangement that does not admit an operation someone expected
— a mismatch between intent and configuration that is otherwise visible
only as an error returned to a caller who may discard it.

The record is written through KACS, so its `emitter.class` is `kacs`.

The refusals that count are one explicit list: `EROFS`, `EXDEV`, `ENOTDIR`,
`EISDIR`, `ENOTEMPTY`, `EEXIST` and `EINVAL`. Call sites cover every
mutating path.

**`EACCES` is deliberately absent.** A refusal produced by an access check
is recorded by the mechanism that performed it, so StrataFS does not
duplicate it. Looking here for a permission denial finds nothing — look at
`kacs.audit.access.checked`.

There is one exception, and it is deliberate. A refused **deferred**
deletion is recorded on any non-zero result, including one refused by an
access check, because by the time a deferred deletion fails there is nobody
left to receive the error. Rollbacks arrive under this type with the same
flag set: a create or link whose outer bookkeeping failed and whose lower
object could not be removed again, and a failed publication rollback after
a copy-up.

Resolution, revalidation and enumeration record nothing at all. They happen
on every path operation, reveal nothing the resulting access check does
not, and recording them would produce volume out of all proportion to their
significance.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.file.path-relative`](~peios/events/field-index/fields-object#object.file.path-relative) | `str.path` | required | The path of the object within its mount, `/`-prefixed. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | StrataFS names its own operations, and the set is disjoint from the `file.` names an already-open handle uses.<br><br>Values here (open set): `copy-file-range` · `copy-up-publication-rollback` · `create` · `create-rollback` · `fallocate` · `link` · `link-rollback` · `mmap` · `remap-file-range` · `removexattr` · `rename` · `rmdir` · `setattr` · `setxattr` · `splice-write` · `supersede` · `supersede-publication` · `tmpfile` · `truncate` · `unlink` · `write`. |
| [`source.stratum.index`](~peios/events/field-index/fields-source#source.stratum.index) | `uint` | optional | Absent when the refusal was raised before any provider was determined. |
| [`source.stratum.path`](~peios/events/field-index/fields-source#source.stratum.path) | `str.path` | optional | Present exactly when `source.stratum.index` is. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | The error the operation failed with, as a negative errno. |
| [`outcome.deferred`](~peios/events/field-index/fields-outcome#outcome.deferred) | `bool` | required | Whether the refusal was deferred — set on rollbacks and on deferred deletions, which are the records where no caller remained to be told. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

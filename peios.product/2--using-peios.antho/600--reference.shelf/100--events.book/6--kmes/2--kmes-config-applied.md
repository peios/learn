---
title: "kmes.config.applied"
description: "The record that KMES read its configuration key and committed what it found."
---

- **Event type:** `kmes.config.applied`
- **Defined in:** `kmes.evman`
- **Tier:** standard
- **Gating:** none — every configuration read that reaches the commit is recorded
- **Cardinality:** once per read of `Machine\System\KMES`

The record that KMES read its configuration key and committed what it
found. Emitted after every read that gets as far as the commit: at boot
once the registry is available, and again each time a value under the key
changes.

The four counts account for every setting the read saw, so a record whose
`config.counts.applied` is zero is a read that changed nothing, and one
with `config.counts.retained-invalid` above zero comes with a
`kmes.config.value.rejected` for each value kept back. A read whose
`BufferCapacity` swap failed is still recorded here, because the other
three settings commit without it; `buffer.capacity` is then the capacity
kept, beside the `kmes.buffer.swap.failed` that says why.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`config.key.path`](~peios/events/field-index/fields-config#config.key.path) | `str` | required | Always `Machine\System\KMES`. |
| [`config.counts.applied`](~peios/events/field-index/fields-config#config.counts.applied) | `uint` | required | How many settings in a configuration refresh were applied. |
| [`config.counts.retained-missing`](~peios/events/field-index/fields-config#config.counts.retained-missing) | `uint` | required | How many settings kept their previous value because they were absent from the registry. |
| [`config.counts.retained-invalid`](~peios/events/field-index/fields-config#config.counts.retained-invalid) | `uint` | required | How many settings kept their previous value because the stored value was rejected, of the wrong type or out of range. |
| [`config.counts.ignored-unknown`](~peios/events/field-index/fields-config#config.counts.ignored-unknown) | `uint` | required | How many registry values were ignored because their names match no setting. |
| [`buffer.capacity`](~peios/events/field-index/fields-buffer#buffer.capacity) | `uint.bytes` | required | The per-CPU ring capacity in force after the commit. |
| [`emission.rate-limit`](~peios/events/field-index/fields-emission#emission.rate-limit) | `uint` | required | The per-process emission ceiling in force after the commit. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

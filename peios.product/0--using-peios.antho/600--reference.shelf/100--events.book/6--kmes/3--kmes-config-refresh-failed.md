---
title: "kmes.config.refresh.failed"
description: "The record that KMES could not read one of its configuration keys and kept running on what it had."
---

- **Event type:** `kmes.config.refresh.failed`
- **Defined in:** `kmes.evman`
- **Tier:** essential
- **Gating:** none — every failed re-read is recorded
- **Cardinality:** once per failed read

The record that KMES could not read one of its configuration keys and kept
running on what it had. Two keys are read this way: `Machine\System\KMES`,
KMES's own settings, and `Machine\Generic\Events`, the emission policy
that decides which kernel event types are written.

A failed read changes nothing. KMES keeps the configuration it last
committed, or the compiled-in defaults if it never committed one, and the
emission policy keeps the switches it last computed, or the tier defaults.
**Until the next change under the key, the registry and the running
kernel disagree**, and this record is the only sign of it: an
administrator who switched an event type off and finds it still written
is looking for one of these.

The usual cause is the registry source failing to answer in time. A
configuration rejected value by value is not a failed read; that is
`kmes.config.value.rejected`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`config.key.path`](~peios/events/field-index/fields-config#config.key.path) | `str` | required | `Machine\System\KMES` or `Machine\Generic\Events`. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | required | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

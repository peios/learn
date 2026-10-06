---
title: "lcs.config.value.rejected"
description: "The record that LCS read one of its own configuration values, rejected it, and carried on with what it had."
---

- **Event type:** `lcs.config.value.rejected`
- **Defined in:** `lcs.evman`
- **Tier:** standard
- **Gating:** none — every rejected configuration value is recorded
- **Cardinality:** once per rejected value

The record that LCS read one of its own configuration values, rejected it,
and carried on with what it had. Identical in shape and meaning to
`kmes.config.value.rejected`, differing only in which key the values live
under.

Validation is reject-or-keep and never clamps, so this event is the only
place where what an administrator wrote and what LCS is running on can be
seen to differ.

Emission failure preserves the retained configuration — a failure to record
the rejection must not change which value is in force.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`config.key.path`](~peios/events/field-index/fields-config#config.key.path) | `str` | required | The registry key the reported value lives under, in canonical form. |
| [`config.name`](~peios/events/field-index/fields-config#config.name) | `str` | required | The name of the configuration value being reported on, within `config.key.path`. |
| [`config.expected.type`](~peios/events/field-index/fields-config#config.expected.type) | `uint.enum` | required | The registry type the value is required to have. |
| [`config.expected.min`](~peios/events/field-index/fields-config#config.expected.min) | `uint` | required | The smallest value accepted for this setting. |
| [`config.expected.max`](~peios/events/field-index/fields-config#config.expected.max) | `uint` | required | The largest value accepted for this setting. |
| [`config.received.kind`](~peios/events/field-index/fields-config#config.received.kind) | `str.enum` | required | How the stored value failed validation. |
| [`config.received.type`](~peios/events/field-index/fields-config#config.received.type) | `uint.enum` | when `config.received.kind == wrong-type` | The registry type the value actually had. |
| [`config.received.value`](~peios/events/field-index/fields-config#config.received.value) | `uint` | when `config.received.kind == out-of-range` | The value that was stored and rejected. |
| [`config.value`](~peios/events/field-index/fields-config#config.value) | `uint` | required | The value retained. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

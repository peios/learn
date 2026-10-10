---
title: "kmes.config.value.rejected"
description: "The record that KMES read a configuration value, rejected it, and carried on with what it had."
---

- **Event type:** `kmes.config.value.rejected`
- **Defined in:** `kmes.evman`
- **Tier:** essential
- **Gating:** none — every rejected configuration value is recorded
- **Cardinality:** once per rejected value

The record that KMES read a configuration value, rejected it, and carried
on with what it had. Emitted when the stored value is missing, of the wrong
type, or out of range.

Validation is **reject-or-keep, never clamp**: a valid value is applied and
an invalid one is ignored, with the last known-good value retained. That
makes this event the only place the divergence is visible — the registry
records what an administrator wrote, and this records what KMES is running
on. An operator reading only the registry will believe a change took effect
that did not.

These records are emitted before the configuration commit and are
deliberately not part of the commit decision: a failure to construct one
must never roll back a hot-swap that otherwise succeeded.

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

*Generated from `kmes.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

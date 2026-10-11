---
title: "eventd.config.changed"
description: "The record that eventd applied a change to one of its configuration values at runtime."
---

- **Event type:** `eventd.config.changed`
- **Defined in:** `eventd.evman`
- **Tier:** essential
- **Gating:** none — every applied change is recorded
- **Cardinality:** once per configuration value whose change was applied

The record that eventd applied a change to one of its configuration values
at runtime. A change to retention or to the stores is a change to what the
audit trail keeps, which is why this is essential.

Every value eventd reloads at runtime is a `REG_DWORD` or a `REG_QWORD`, so
each side of a change is an integer or absent. A side is absent when no
value is stored, even though eventd's compiled default then applies. A
stored value of the wrong type is reported as the expected type, holding
the integer eventd actually uses.

Replaces `synthetic.config_change` (PEI-617). Its values were decimal
strings and its absent values nil.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`config.key.path`](~peios/events/field-index/fields-config#config.key.path) | `str` | required | Always `Machine\System\eventd`. |
| [`config.name`](~peios/events/field-index/fields-config#config.name) | `str` | required | The name of the configuration value being reported on, within `config.key.path`. |
| [`config.type`](~peios/events/field-index/fields-config#config.type) | `uint.enum` | optional | Absent when the change removed the value. Present exactly when `config.value` is. |
| [`config.type-previous`](~peios/events/field-index/fields-config#config.type-previous) | `uint.enum` | optional | Absent when the value was not set before. Present exactly when `config.value-previous` is. |
| [`config.value`](~peios/events/field-index/fields-config#config.value) | `uint` | optional | The value in force after the event. |
| [`config.value-previous`](~peios/events/field-index/fields-config#config.value-previous) | `uint` | optional | The value that was in force before the change. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `eventd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

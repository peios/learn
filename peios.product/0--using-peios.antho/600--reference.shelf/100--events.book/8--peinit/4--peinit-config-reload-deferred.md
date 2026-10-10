---
title: "peinit.config.reload.deferred"
description: "A configuration reload during the boot window changed definitions of services the boot plan had not yet launched."
---

- **Event type:** `peinit.config.reload.deferred`
- **Defined in:** `peinit.evman`
- **Tier:** verbose
- **Gating:** none
- **Cardinality:** once per reload during the boot window that left definitions pending

A configuration reload during the boot window changed definitions of
services the boot plan had not yet launched. The boot runs against its
snapshot, so those services start from the plan, and the change waits for
`peinit.config.reload.applied`.

Formerly `config.reload_deferred`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`graph.services`](~peios/events/field-index/fields-graph#graph.services) | `str[]` | required | The services whose definitions were deferred. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

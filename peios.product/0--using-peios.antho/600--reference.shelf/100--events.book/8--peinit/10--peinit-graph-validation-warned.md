---
title: "peinit.graph.validation.warned"
description: "The service graph passed validation with a warning: nothing was refused, but something will not behave as its author probably expects."
---

- **Event type:** `peinit.graph.validation.warned`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every warning is recorded
- **Cardinality:** one per warning

The service graph passed validation with a warning: nothing was refused,
but something will not behave as its author probably expects.

Formerly `graph.validation_warning`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`graph.phase`](~peios/events/field-index/fields-graph#graph.phase) | `str.enum` | required | When the service graph was validated. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | The warning.<br><br>Values here (open set): `alive-readiness-with-hard-dependents` · `unfilled-role`. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | when `outcome.reason == alive-readiness-with-hard-dependents` | The name of the service the event is about, as its definition names it. |
| [`object.service.dependents`](~peios/events/field-index/fields-object#object.service.dependents) | `str[]` | when `outcome.reason == alive-readiness-with-hard-dependents` | The services that hard-depend on this one, by name. |
| [`graph.role`](~peios/events/field-index/fields-graph#graph.role) | `str` | when `outcome.reason == unfilled-role` | The role no service fills. |
| [`graph.services`](~peios/events/field-index/fields-graph#graph.services) | `str[]` | when `outcome.reason == unfilled-role` | The services a graph finding involves. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

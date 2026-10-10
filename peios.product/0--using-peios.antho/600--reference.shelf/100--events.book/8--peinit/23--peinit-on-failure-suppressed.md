---
title: "peinit.on-failure.suppressed"
description: "peinit declined to start an OnFailure handler, because starting it would have looped or gone too deep, so the failure it was meant to handle went unhandled."
---

- **Event type:** `peinit.on-failure.suppressed`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every suppressed handler is recorded
- **Cardinality:** one record per occurrence

peinit declined to start an OnFailure handler, because starting it would
have looped or gone too deep, so the failure it was meant to handle went
unhandled.

Formerly `on_failure.loop_suppressed`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | required | The service whose failure the chain was handling. |
| [`object.service.on-failure.name`](~peios/events/field-index/fields-object#object.service.on-failure.name) | `str` | required | The OnFailure handler peinit declined to start, because starting it would have looped or gone too deep. |
| [`object.service.on-failure-chain`](~peios/events/field-index/fields-object#object.service.on-failure-chain) | `str[]` | required | The OnFailure handlers already started in the chain that peinit cut short, in the order they were started. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | Why the operation resolved the way it did.<br><br>Values here (closed set): `cycle` · `max-depth`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

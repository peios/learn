---
title: "peinit.boot.downgraded"
description: "A full boot was downgraded to safe mode: the machine is running a reduced service set."
---

- **Event type:** `peinit.boot.downgraded`
- **Defined in:** `peinit.evman`
- **Tier:** essential
- **Gating:** none
- **Cardinality:** one per finding that forced the downgrade, at most once a boot in all

A full boot was downgraded to safe mode: the machine is running a reduced
service set. The services named are not marked failed, because safe mode
never meant to start them, so this record is the only one that names them
as the cause. Essential because it is rare and changes what the whole
machine is running.

Formerly `boot.safe_mode_downgrade`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | The finding that forced the downgrade.<br><br>Values here (open set): `critical-cycle` · `critical-boot-conflict`. |
| [`graph.services`](~peios/events/field-index/fields-graph#graph.services) | `str[]` | when `outcome.reason == critical-cycle` | The services a graph finding involves. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | when `outcome.reason == critical-boot-conflict` | The name of the service the event is about, as its definition names it. |
| [`object.service.conflict.name`](~peios/events/field-index/fields-object#object.service.conflict.name) | `str` | when `outcome.reason == critical-boot-conflict` | The name of the service this one conflicts with, on a finding that two services both triggered at boot declare a conflict and so cannot both start. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

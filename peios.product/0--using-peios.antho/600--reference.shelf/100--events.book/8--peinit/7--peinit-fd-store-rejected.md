---
title: "peinit.fd-store.rejected"
description: "peinit refused a file descriptor a service asked it to keep."
---

- **Event type:** `peinit.fd-store.rejected`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none — every refused descriptor is recorded
- **Cardinality:** one record per occurrence

peinit refused a file descriptor a service asked it to keep.

Formerly `fd_store.rejected`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | required | The name of the service the event is about, as its definition names it. |
| [`object.fd-store.name`](~peios/events/field-index/fields-object#object.fd-store.name) | `str` | required | The name a service gave a file descriptor it asked peinit to keep, with `FDNAME=`. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | `disabled` when the service's definition does not enable an fd store; `full` when it is at its limit.<br><br>Values here (open set): `disabled` · `full`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

---
title: "peinit.service.abandoned"
description: "A service's processes survived SIGKILL and its post-kill timeout, so peinit gave up on them and moved the service to abandoned: its cgroup is still populated, unkillably."
---

- **Event type:** `peinit.service.abandoned`
- **Defined in:** `peinit.evman`
- **Tier:** standard
- **Gating:** none
- **Cardinality:** once per service abandoned

A service's processes survived SIGKILL and its post-kill timeout, so peinit
gave up on them and moved the service to `abandoned`: its cgroup is still
populated, unkillably. Written only on the shutdown path so far; the
name also covers an abandonment anywhere else.

Formerly `shutdown.abandoned`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | required | The name of the service the event is about, as its definition names it. |
| [`object.cgroup.path`](~peios/events/field-index/fields-object#object.cgroup.path) | `str.path` | required | The cgroup the event is about, as its full path under `/sys/fs/cgroup/peinit`. |
| [`object.service.state-previous`](~peios/events/field-index/fields-object#object.service.state-previous) | `str.enum` | required | The service's state before the event, with the same values as `object.service.state`. |
| [`object.service.state`](~peios/events/field-index/fields-object#object.service.state) | `str.enum` | required | Always `abandoned`. |
| [`object.service.transition-cause`](~peios/events/field-index/fields-object#object.service.transition-cause) | `str.enum` | required | Why the service's state changed. |
| [`object.service.generation`](~peios/events/field-index/fields-object#object.service.generation) | `uint` | required | The service's activation generation: a counter peinit advances each time the service enters `starting`, so that every incarnation of a service has its own number. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

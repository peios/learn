---
title: "peinit.graph.operation.ended"
description: "An operation that is a member of a graph execution context reached its terminal outcome as the graph sees it: satisfied, so that what depends on it may proceed, or failed."
---

- **Event type:** `peinit.graph.operation.ended`
- **Defined in:** `peinit.evman`
- **Tier:** verbose
- **Gating:** none — every member of a graph context is recorded
- **Cardinality:** one record per occurrence

An operation that is a member of a graph execution context reached its
terminal outcome as the graph sees it: satisfied, so that what depends on
it may proceed, or failed. The operation's own `peinit.operation.ended`
records the same end from the operation's side.

Formerly `graph.operation_terminal`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`graph.context`](~peios/events/field-index/fields-graph#graph.context) | `uint` | required | The graph execution context an event belongs to: one boot's start of its service set, or one on-demand start of a service and everything it needs. |
| [`object.operation.guid`](~peios/events/field-index/fields-object#object.operation.guid) | `bin.guid` | required | The peinit operation the event is about: a start, stop, restart, reload or reset of one service, from the moment it is requested to the moment it ends. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | required | The name of the service the event is about, as its definition names it. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True when the graph counts the member satisfied, false when it failed. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

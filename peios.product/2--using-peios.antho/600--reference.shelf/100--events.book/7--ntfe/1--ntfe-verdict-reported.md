---
title: "ntfe.verdict.reported"
description: "The record of a traffic policy decision that a rule explicitly asked to be reported."
---

- **Event type:** `ntfe.verdict.reported`
- **Defined in:** `ntfe.evman`
- **Tier:** standard
- **Gating:** an explicit report directive in the matching rule
- **Cardinality:** once per matching evaluation

The record of a traffic policy decision that a rule explicitly asked to be
reported. Not a record of every decision — the engine evaluates constantly
and reports only where a rule says to.

**A stock machine emits none of these.** The shipped baseline rule set
contains no report directives, so this event exists and never fires until
an administrator adds one. Absence of these records says nothing about
whether traffic was evaluated.

The engine's own record of every verdict goes to a private ring read by the
userspace policy daemon, not to the event stream, and is overwritten when
no reader is attached. So the complete decision history is neither in the
event stream nor durable.

Address, port and protocol fields are conditional on how far up the stack
evaluation reached: traffic matched at the raw-packet layer has no
addresses to record.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`rule.name`](~peios/events/field-index/fields-rule#rule.name) | `str` | required | The policy rule that produced this record, by name. |
| [`rule.hash`](~peios/events/field-index/fields-rule#rule.hash) | `uint` | required | The FNV-1a-64 hash of the rule's whole registry path. |
| [`rule.name-truncated`](~peios/events/field-index/fields-rule#rule.name-truncated) | `bool` | optional | Whether `rule.name` was cut short because the rule's path did not fit in the record. |
| [`rule.report-level`](~peios/events/field-index/fields-rule#rule.report-level) | `uint` | required | The reporting level the matching rule asked for. |
| [`rule.layer`](~peios/events/field-index/fields-rule#rule.layer) | `str.enum` | required | Which evaluation layer the rule sat in. |
| [`rule.seat`](~peios/events/field-index/fields-rule#rule.seat) | `str.enum` | required | Where in the path evaluation happened. |
| [`outcome.verdict`](~peios/events/field-index/fields-outcome#outcome.verdict) | `str.enum` | required | The decision a policy engine reached, where the decision has more than two states and `outcome.success` cannot express it. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.verdict == reject` | Which flavour of explicit rejection the rule asked for: the story the REJECT tells the sender. `refused` says nothing is listening and reveals no policy; `prohibited` says policy refused the traffic. When two REJECTs tie on priority, `refused` wins.<br><br>Values here (closed set): `prohibited` · `refused`. |
| [`network.direction`](~peios/events/field-index/fields-network#network.direction) | `str.enum` | required | Which way the traffic was moving relative to this machine. |
| [`network.interface.name`](~peios/events/field-index/fields-network#network.interface.name) | `str` | optional | Absent when the traffic was evaluated with no device attached, in which case `network.interface.index` is 0. |
| [`network.interface.index`](~peios/events/field-index/fields-network#network.interface.index) | `uint` | required | The kernel's index for that interface. |
| [`network.ether-type`](~peios/events/field-index/fields-network#network.ether-type) | `uint` | required | The link-layer protocol number of the frame. |
| [`network.family`](~peios/events/field-index/fields-network#network.family) | `uint.enum` | required | The address family of the addresses in this record. |
| [`network.protocol`](~peios/events/field-index/fields-network#network.protocol) | `uint.enum` | when `network.family != 0` | The transport protocol number, from the IANA protocol numbers registry. |
| [`source.address`](~peios/events/field-index/fields-source#source.address) | `str.ip` | when `network.family != 0` | The address the traffic came from, rendered in the textual form for its family. |
| [`destination.address`](~peios/events/field-index/fields-destination#destination.address) | `str.ip` | when `network.family != 0` | The address the traffic was going to, rendered in the textual form for its family. |
| [`source.port`](~peios/events/field-index/fields-source#source.port) | `uint` | optional | Present when the protocol has ports. |
| [`destination.port`](~peios/events/field-index/fields-destination#destination.port) | `uint` | optional | Present when the protocol has ports. |
| [`flow.state`](~peios/events/field-index/fields-flow#flow.state) | `str.enum` | optional | Present when flow tracking applied. |
| [`network.length`](~peios/events/field-index/fields-network#network.length) | `uint.bytes` | required | The length of the traffic unit evaluated. |
| [`policy.generation`](~peios/events/field-index/fields-policy#policy.generation) | `uint` | required | The generation counter of the rule set in force when the decision was made. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

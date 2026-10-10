---
title: "ntfe.policy.published"
description: "The record that a new generation of traffic rules went into force."
---

- **Event type:** `ntfe.policy.published`
- **Defined in:** `ntfe.evman`
- **Tier:** standard
- **Gating:** none — every generation of rules that goes into force is recorded
- **Cardinality:** once per published generation of rules

The record that a new generation of traffic rules went into force. The
kernel reads its own policy from `Machine\System\Network\Rules`, a short
while after the registry changes, and publishes it whole: from this point
every traversal is judged by these rules, and every flow judged under the
old ones is judged again on its next packet.

A re-read that finds the policy exactly as it was published publishes
nothing and writes no record, so writing a rule back unchanged, or netd
writing its inventory, is silent. A refused policy writes
`ntfe.policy.rejected` instead, and the generation before it stays.

**Not every generation has one of these.** A change to the network context
(which network each interface is on, and its trust) advances the same
generation counter without a new rule set, and writes no record. A verdict
whose `policy.generation` falls between two of these records was judged by
the rules of the earlier one.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`policy.generation`](~peios/events/field-index/fields-policy#policy.generation) | `uint` | required | The generation this policy now runs as. Verdict records carry the same number. |
| [`policy.generation-previous`](~peios/events/field-index/fields-policy#policy.generation-previous) | `uint` | required | The generation of the rule set this one replaced, or 0 when this is the first since boot. Context changes advance the counter too, so it can be lower than one less than `policy.generation`. |
| [`policy.layers`](~peios/events/field-index/fields-policy#policy.layers) | `str.enum[]` | required | The rules layers the active generation loaded a forest for. |
| [`policy.report-threshold`](~peios/events/field-index/fields-policy#policy.report-threshold) | `uint` | required | The machine's reporting threshold, `CurrentReportingLevel`: a rule's report fires only when its level is at least this. |
| [`policy.report-threshold-previous`](~peios/events/field-index/fields-policy#policy.report-threshold-previous) | `uint` | required | 1, the default, when this is the first generation since boot. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

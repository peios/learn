---
title: "lcs.source.response.rejected"
description: "The record that LCS rejected data a registry source sent it."
---

- **Event type:** `lcs.source.response.rejected`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** none — every rejection is recorded
- **Cardinality:** one record per occurrence

The record that LCS rejected data a registry source sent it. Sources are
userspace backends serving configuration into the kernel, so this is the
boundary where the kernel refuses to believe what userspace told it.

**This is the one LCS event with no caller.** It describes a source
misbehaving rather than a principal acting, and there is frequently no
principal involved — the data arrived on a source channel, not through a
syscall.

The failure classes distinguish malformed structure from semantic
impossibility: a security descriptor that will not parse is a different
problem from a sequence number from the future or two layers claiming the
same winning sequence.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`source.rsi.slot`](~peios/events/field-index/fields-source#source.rsi.slot) | `uint` | required | Which registry source slot supplied the data, by index. |
| [`source.rsi.hive`](~peios/events/field-index/fields-source#source.rsi.hive) | `str` | optional | The hive the offending source data belonged to, where the failure could be attributed to one. |
| [`request.id`](~peios/events/field-index/fields-request#request.id) | `uint` | optional | The identifier of the source request this record concerns, for joining a record to the exchange that produced it. |
| [`request.op-code`](~peios/events/field-index/fields-request#request.op-code) | `uint` | optional | The source-protocol operation code of the request this record concerns. |
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | optional | Present when the rejected data could be attributed to a specific key. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | required | The source-validation failure class.<br><br>Values here (open set): `malformed-security-descriptor` · `malformed-layer-name` · `unknown-rsi-status-code` · `future-sequence-number` · `duplicate-winning-sequence-tie` · `malformed-layer-metadata-security-descriptor` · `malformed-key-name` · `malformed-value-name` · `malformed-response-payload` · `malformed-key-metadata` · `malformed-value-payload` · `malformed-delete-layer-orphan-list`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

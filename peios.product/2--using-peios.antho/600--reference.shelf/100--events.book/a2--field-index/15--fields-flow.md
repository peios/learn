---
title: "flow.*"
description: "Every field the evman catalogue defines under flow: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `flow`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="flow.endpoint"></a>`flow.endpoint`

- **Type:** `str.enum`
- **Values:** `source` · `destination`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Which end of the flow the record concerns: the local endpoint the flow
layer judged. Outbound traffic is judged for its source and inbound traffic
for its destination; a loopback flow has two local ends and is judged once
for each, and this field is what tells those two records apart.

**Carried by:**

No event carries this field yet.

## <a id="flow.id"></a>`flow.id`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Conntrack's identifier for the flow. **Not emitted today**: the flows dump
carries it but the verdict record does not, so a verdict cannot be joined
to the flow it was passed on. Unique only among flows alive at the same
time.

**Carried by:**

No event carries this field yet.

## <a id="flow.rule.hash"></a>`flow.rule.hash`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The hash of the path of the rule behind a flow's cached verdict: the
FNV-1a-64 hash of the whole registry path, kept in the flow's sentence. The
sentence keeps no path, so after a re-judgment this is the only thing that
survives about the rule that previously decided the flow. Resolve it
against the generation that wrote the sentence, because a later generation
may name its rules differently. It is the same value a report carries as
`rule.hash`.

**Carried by:**

No event carries this field yet.

## <a id="flow.state"></a>`flow.state`

- **Type:** `str.enum`
- **Values:** `new` · `established` · `related` · `invalid` · `untracked`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

How connection tracking classified this traffic. `untracked` means
connection tracking gave the traffic no flow state NTFE recognises:
tracking was not applied, or conntrack judged the packet incoherent. Absent
at the ingress seat, which stands before connection tracking.

**`invalid` is not produced today.** It is reserved for traffic that
tracking applied to and found fitting no known flow, but telling that apart
needs conntrack's own verdict, which NTFE does not read yet, so incoherent
traffic reports `untracked`. The value stays listed because the enumeration
is closed and its values are part of the ABI.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="flow.verdict-expiry"></a>`flow.verdict-expiry`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

When a flow's cached verdict stops being valid, because a time condition
the judgment consulted will next change its answer. The flow is re-judged
on its first packet after this time. Absent when the verdict has no time
edge, though it is still re-judged when a new generation lands. The kernel
holds this to the whole second.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

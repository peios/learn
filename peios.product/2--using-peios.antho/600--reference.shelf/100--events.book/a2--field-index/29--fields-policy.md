---
title: "policy.*"
description: "Every field the evman catalogue defines under policy: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `policy`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="policy.fallback"></a>`policy.fallback`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the compiled-in fallback policy was answering rather than a loaded
rule set. Makes a silent fall-back to built-in security policy visible: the
system keeps working, on rules no administrator wrote.

**Carried by:**

No event carries this field yet.

## <a id="policy.generation"></a>`policy.generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The generation counter of the rule set in force when the decision was made.
Increments on every policy load, so a record can be tied to the exact rule
set that produced it rather than to whatever is loaded when the record is
read.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="policy.generation-previous"></a>`policy.generation-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The generation that was in force before a policy load replaced it. On a
failed load, compare with `policy.previous-retained`.

**Carried by:**

No event carries this field yet.

## <a id="policy.layers"></a>`policy.layers`

- **Type:** `str.enum[]`
- **Values:** `raw-packet` · `packet` · `flow`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The rules layers the active generation loaded a forest for. A layer missing
from the list judges nothing and waves every traversal past it. **A missing
`flow` layer also turns off endpoint attribution for the whole machine**,
so no flow carries an owner and every identity field is absent.

**Carried by:**

No event carries this field yet.

## <a id="policy.previous-retained"></a>`policy.previous-retained`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a failed policy load left the previous rule set in force. True is
the safe outcome: the old policy still applies. False means the previous
rule set is not in force either; `policy.fallback` says what is answering
instead.

**Carried by:**

No event carries this field yet.

## <a id="policy.report-threshold"></a>`policy.report-threshold`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The machine's reporting threshold, `CurrentReportingLevel`: a rule's report
fires only when its level is at least this. It runs from 1 to 6 and is 1
when the registry has no value. Rules may only declare levels 1 to 5, so a
threshold of 6 silences every report on the machine, and a silent stream
then means nothing about the traffic.

**Carried by:**

No event carries this field yet.

## <a id="policy.report-threshold-previous"></a>`policy.report-threshold-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The machine's reporting threshold before the change a record reports, in
the terms of `policy.report-threshold`. A move to 6 is a change to the
audit volume itself and turns every network report off.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*

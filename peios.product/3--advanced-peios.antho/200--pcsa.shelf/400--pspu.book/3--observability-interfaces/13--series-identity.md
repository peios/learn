---
title: Series Identity
description: What makes two samples the same time series — name, labels and histogram boundaries — and what pointedly does not participate.
---

Two samples belong to the same time series when they agree on:

- the **name**, compared exactly, byte for byte; and
- the **label set**, compared as an unordered set of key-value pairs,
  each compared exactly; and
- for histograms, the **bucket boundaries**, compared as an ordered
  sequence of binary64 values.

Nothing else participates. Type does not: a record whose type disagrees
resolves to the series and is then discarded for disagreeing (§3.10).
Boot ID does not: a series continues across a reboot, and a client that
wants one boot's worth filters for it (§3.25). Time does not.

## Order does not distinguish a label set

`{core: "0", host: "a"}` and `{host: "a", core: "0"}` are the same
series. A collector MUST compare label sets as sets.

To do so it needs a canonical form, and the form in use is the reason
label values may not contain `=` or `,` (§3.10): pairs are sorted by key
in unsigned UTF-8 byte order, each written `key=value`, and joined with
commas. Because neither delimiter can occur inside a key or a value, no
escaping is needed and no two distinct label sets can produce the same
string.

The byte form itself is the collector's business and this chapter does
not require it. What it requires is the property: **a label set has
exactly one identity, independent of the order the producer wrote it
in.** The delimiter reservation is stated normatively because it binds
the *producer*, and a producer cannot see the encoding that motivates it.

## Absent labels and empty labels

A record with no `labels` field, a record with an empty `labels` map,
and a record whose labels were all discarded are the same series: the
one with no labels. There is no distinction between "unlabelled" and
"labelled with nothing".

## Boundaries are identity, not metadata

Two histogram samples with different boundaries are different series
even when name and labels agree.

This is the consequence that surprises producers, and it is unavoidable:
cumulative counts against one set of bucket edges cannot be compared
with counts against another, so calling them one series would mean
computing percentiles across incommensurable distributions. A producer
that re-tunes its buckets each collection cycle creates a series each
cycle, each holding a single sample and each surviving until retention
removes it.

A collector MUST NOT defend against this. It is a producer defect, it is
indistinguishable at the interface from legitimately introducing a new
metric, and every defence available — capping series, merging near-equal
boundary sets, rejecting a second boundary set for a name — would break
a correct producer to inconvenience an incorrect one.

## Series are created, never announced

A series comes into existence when its first sample arrives. There is no
registration message, no schema, and no way to declare a series in
advance or to retire one.

A collector MUST NOT require a series to be known before a sample of it
is accepted, and MUST NOT limit how many series exist. A series with no
remaining samples ceases to exist when retention removes the last of
them; nothing else removes one.

> [!NOTE]
> The absence of a cap is a deliberate and load-bearing decision, and it
> is worth being clear about what it costs. Labels are producer-supplied
> and are not part of publication authorization (§3.9), so a producer
> authorized for one metric name can create series beneath that name
> without limit, and each persists until the retention window elapses.
> Name authorization bounds the namespace, not its label cardinality.

## Gaps are preserved

A collector MUST NOT interpolate, backfill, or synthesise a sample that
a producer did not send.

A missing sample is a real fact about the system — the producer was
down, the datagram was dropped, the sweep was late — and it is a fact
the metric is often being watched for. A series with a hole in it is
returned with a hole in it, and a client that wants a value across the
hole computes one itself.

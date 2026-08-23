---
title: Validating a Metric Record
description: What causes a metric datagram or a single record to be discarded, silently, and why the timestamp rule differs from the log channel's.
---

Failures on this channel are silent, exactly as on the log channel
(§3.4, §3.8). The scopes are the same, with one difference that matters:
**a metric record has no ignorable field.** Every field a metric record
carries participates either in the series identity or in the
measurement, so there is nothing whose loss leaves a usable record
behind. A malformed `timestamp` costs the log line nothing and costs the
sample everything.

## The datagram is discarded

- it is not valid MessagePack
- it decodes to something that is neither a map nor an array of maps
- the kernel reported it truncated (§3.9)

## The record is discarded

A collector MUST discard a record, leaving the rest of its batch
untouched, for any of the following.

**Structure**

- a required field is absent, or has the wrong type
- the map contains a duplicate top-level key
- `type` is not exactly `"counter"`, `"gauge"` or `"histogram"`

**Name and labels** (§3.10)

- `name` is empty or does not match the identifier grammar
- a label key or value is not a string, or is empty
- a label key does not match the identifier grammar
- a label value contains `=` or `,`
- a label key is repeated within the record
- a label key is one of `timestamp`, `boot_id`, `name`, `type`, `value`

**Timestamp**

- `timestamp` is present and is not an integer, is negative, or is
  outside the timestamp domain (§3.5)

**Counter and gauge values**

- the value is not a number
- it converts to a non-finite binary64
- it is negative and the type is counter

**Histogram values**

- the value is not a map, or its map has a duplicate key
- a field is absent or has the wrong type
- `boundaries` is empty
- a boundary or `sum` converts to a non-finite binary64
- `counts` and `boundaries` differ in length
- the converted boundaries are not strictly increasing
- a count is negative, the counts are not non-decreasing, or a count
  exceeds `total_count`
- `total_count` is zero and any count or `sum` is non-zero

**Series consistency**

- the record resolves to an existing series whose type differs (§3.10)

## Why the timestamp rule differs from logs

On the log channel a malformed timestamp is ignored and the record
kept; here it discards the record.

The asymmetry is not an inconsistency. A log line with the wrong time is
still the line, and reading it is still worth doing. A sample is a
`(time, value)` pair and nothing else: attaching the collector's receipt
time to a measurement taken at an unknown moment does not recover the
sample, it fabricates one, and it fabricates one that will be charted
next to real ones. Discarding leaves a gap, which is honest (§3.4).

Absence is different from malformation. A record that simply omits
`timestamp` is asserting "now", and the collector's clock is the right
answer to that.

## Silence, again

A collector MUST NOT emit an event, log an error, or increment anything
a client can observe in response to any failure in this article — with
no exception for the series-consistency failure, which is the one that
most looks like it deserves one.

A producer that changes a metric's type is misconfigured, and the
misconfiguration is permanent and invisible: every sample is discarded
for as long as the series exists. The only signal available to an
operator is that the series stopped advancing while the producer
reported no error, and the only diagnosis is to query the series and
read its `type` (§3.25).

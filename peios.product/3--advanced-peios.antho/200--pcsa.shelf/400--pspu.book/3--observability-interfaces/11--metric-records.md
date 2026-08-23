---
title: Metric Records
description: The MessagePack map that carries one metric sample, the histogram value shape, and why type is per record rather than per series.
---

A metric datagram carries one record, encoded as a MessagePack map, or
several, encoded as an array of maps. A collector MUST accept both
(§3.9). Each map is one sample of one series.

## Fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | The metric name (§3.10). |
| `labels` | map | no | Key-value string pairs. Absent means the series has no labels, which is not the same as a series whose labels are empty — it is the same series. |
| `type` | string | yes | Exactly `"counter"`, `"gauge"` or `"histogram"`, lowercase. |
| `timestamp` | integer | no | When the measurement was taken, in the timestamp domain (§3.5). Absent means the collector uses its own clock at receipt. |
| `value` | varies | yes | The measurement. A number for counter and gauge; a map for histogram. |

A collector MUST ignore fields it does not recognise (§3.29).

## The histogram value

For a histogram, `value` is a map:

| Field | Type | Meaning |
|---|---|---|
| `boundaries` | array of number | Non-empty, finite bucket upper bounds, strictly increasing after conversion to binary64, in the order given. |
| `counts` | array of integer | Cumulative count per boundary. Same length as `boundaries`. Non-decreasing, each no greater than `total_count`. |
| `total_count` | integer | Number of observations. |
| `sum` | number | Finite sum of the observations. |

Counts and `total_count` MUST be MessagePack unsigned integers, or
non-negative signed integers. `boundaries` and `sum` MAY be integers or
floats and are converted as §3.10 requires.

## `type` is per record, not per series

Every record declares its type, including the second and every
subsequent sample of a series that already exists.

This is redundant on the wire and deliberately so. A producer holds no
state about what a collector already knows, has no way to ask, and MUST
NOT be required to establish a series before sampling it: the first
sample of a series and the millionth are the same message. The
redundancy is what makes a producer stateless, and the cost is one short
string per sample.

The collector uses the declaration only on first sight. Afterwards it is
a consistency check, and a record that fails it is discarded (§3.10).

## Timestamps need not increase

A collector MUST store a valid sample whose timestamp is older than
samples it already holds for that series.

Producers batch, clocks step, and a collection sweep may be submitted
out of order or retried. A collector that refused late samples would
turn any of those into silent data loss, so it accepts them and defines
every ordering it performs over `timestamp` rather than over arrival
(§3.21, §3.25). Two samples of one series MAY share a timestamp; the
collector orders them deterministically and a client MUST NOT depend on
which comes first.

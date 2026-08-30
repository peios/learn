---
title: The Metric Data Model
description: What a metric is on this interface — names, labels, and the counter, gauge and histogram types, all valued as binary64.
---

A metric is a quantity that varies and is worth watching over time: a
utilisation, a queue depth, a running total, a distribution of
latencies. Metrics are dense where events and logs are sparse — many
measurements of the same thing rather than a record of a thing that
happened — and the model reflects that.

A **sample** is one measurement, of one time series, at one moment. It
carries:

- a **name**, identifying what is measured
- a **label set**, identifying which instance of it
- a **type**, fixing how the value is to be read
- a **timestamp**
- a **value**, whose shape depends on the type

Name and labels together identify the series (§3.13). The type is a
property of the series, not of the sample.

## Names

A name MUST match the identifier grammar of §3.19:

```text
[A-Za-z_][A-Za-z0-9_.-]*
```

A collector MUST discard a record whose name does not, for the same two
reasons an origin is constrained (§3.7): names are matched against
patterns in which `*` is the wildcard, and names are what read access is
granted on.

Beyond that, naming is convention and a collector MUST NOT enforce any.
The conventions in use are a dot-separated hierarchy from general to
specific, the unit as the last component, and a cumulative name for a
cumulative quantity:

```text
system.cpu.usage
disk.read.bytes
request.duration.seconds
http.requests.total
```

## Labels

Labels are the dimensions of a measurement: which core, which device,
which method. `cpu.usage` with `core="0"` and `cpu.usage` with
`core="1"` are two series, not two samples of one.

Label keys and values MUST be non-empty UTF-8 strings. A key MUST match
the identifier grammar above; a value MUST NOT contain `=` (0x3D) or `,`
(0x2C), which are reserved as delimiters in the collector's canonical
representation of a label set (§3.13). A key MUST NOT be repeated within
one sample, and MUST NOT be any of the five fixed field names a metric
result carries — `timestamp`, `boot_id`, `name`, `type`, `value` —
because labels and fixed fields share one flat namespace in a result
record (§3.22) and a collision would make the record ambiguous.

A record violating any of these is discarded (§3.12).

> [!NOTE]
> Label keys are constrained to the identifier grammar for the reason
> that matters most in practice: a key that cannot be written in a query
> cannot be filtered on, grouped by, or granted access to. A label you
> cannot address is storage you cannot reach.

**Label cardinality is the producer's responsibility.** Each distinct
combination of label values is a distinct series, so labels whose values
are unbounded — request identifiers, user-supplied strings, timestamps —
produce series without limit, and a collector is required neither to cap
them nor to degrade gracefully when they arrive. A producer SHOULD use
labels whose value sets are small and known. A dimension that is not
bounded belongs in an event payload, where it costs one field, not in a
label, where it costs a series.

A collector may bound its total metric storage through retention without
limiting series creation. Peios eventd does this by default: it continues
accepting new series but removes the oldest samples when the metric
store's logical live size exceeds its configured ceiling. That protects
the volume; it does not make high-cardinality labels safe, because an
active set larger than the series cache can still thrash ingestion.

## Types

The type is fixed when the series is first seen and is **immutable**. A
sample that resolves to an existing series but declares a different type
is discarded (§3.12), permanently and without notification. A producer
that changes the type of a metric it already emits has stopped emitting
it, and the only visible symptom is that the series stops advancing.

### Counter

A value that only increases, and resets to zero when the producer
restarts. Used for cumulative quantities: requests served, bytes
transmitted, errors encountered.

A counter value MUST be a finite, non-negative binary64 value.

The raw value is rarely what a reader wants; the rate of change is
(§3.25). A decrease is read as a restart rather than as a negative
change, which is why the type must be declared: the same number sequence
means something different for a gauge.

### Gauge

A value that may move in either direction. Used for current state: a
utilisation, an amount in use, a depth, a temperature.

A gauge value MUST be a finite binary64 value, and MAY be negative.

### Histogram

A distribution of observations across buckets the producer chose. Used
where the shape matters more than the mean — latencies above all.

A histogram value carries:

- **boundaries**: a non-empty array of bucket upper bounds, strictly
  increasing in the order given
- **counts**: one cumulative count per boundary, each being the number
  of observations less than or equal to that boundary; non-decreasing,
  and each no greater than the total
- **total_count**: the number of observations
- **sum**: the finite sum of the observations

Boundaries are part of the series identity (§3.13). A collector MUST NOT
sort or reinterpret them; a producer that changes them has started a new
series, and SHOULD therefore keep them fixed for the life of a metric.

The final count MAY be less than the total: observations above the
highest boundary are the difference between them, and are not otherwise
represented. A total of zero is a valid empty sample, in which case
every count and the sum MUST be zero.

> [!NOTE]
> Observations above the highest boundary are counted but not located.
> A reader asking for a high percentile of a distribution whose tail
> overflows gets no answer rather than a wrong one (§3.25), so a producer
> SHOULD choose a highest boundary above the values it expects to see.

## Values are floating point

Numeric input MAY be a MessagePack integer or a MessagePack float; both
are converted to binary64 with round-to-nearest, ties-to-even. Every
value a collector stores and every value a query returns is a finite
binary64.

Non-finite values are refused rather than stored: a record whose value
converts to NaN or to either infinity is discarded (§3.12). There is no
representation for a missing measurement — a producer with nothing to
report sends nothing, and the gap is the answer (§3.13).

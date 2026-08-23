---
title: Encoding and Time
description: MessagePack on every interface, the canonical subset producers must emit, and how timestamps are carried.
---

## MessagePack

Every structured value on all three interfaces — log records, metric
samples, query requests, query responses — is encoded as MessagePack.
Strings are UTF-8.

The choice is inherited rather than made here: KMES event payloads are a
single MessagePack value, so a collector already carries a decoder and a
query result can carry an event payload outward without re-encoding it.

A decoder MUST accept any valid MessagePack encoding of a value it is
given. In particular a producer MAY use any length-prefix width that can
represent the value, and a collector MUST NOT require the shortest.

## Canonical MessagePack

Where this chapter requires a **canonical** encoding, the value MUST be
encoded as follows:

- Nil and booleans use the fixed singleton encodings.
- Integers use the shortest encoding that preserves signedness:
  non-negative values use positive fixint, `uint8`, `uint16`, `uint32`
  or `uint64`; negative values use negative fixint, `int8`, `int16`,
  `int32` or `int64`.
- Floats are encoded as `float64`. Finite values use their IEEE-754
  binary64 representation; the infinities use the normal binary64
  encodings; **any** NaN is encoded as the single quiet NaN bit pattern
  `0x7ff8000000000000`.
- Strings, binary values, arrays and maps use the shortest length-prefix
  form capable of representing the length.
- Arrays encode each element recursively, in order.
- Maps encode keys and values recursively, with entries sorted by the
  canonical encoded key bytes; ties are broken by the canonical encoded
  value bytes.

Canonical encoding exists so that two values that are equal are also
byte-identical, which is what makes them comparable and orderable
without decoding. It is required in exactly two places: histogram
sample storage, where it makes a sample map a stable value (§3.11), and
array comparison in query ordering and grouping (§3.21).

It does **not** constrain what a producer sends. Ingestion accepts any
valid encoding.

## Timestamps

A timestamp is wall-clock time in **nanoseconds since the Unix epoch,
UTC**, as a signed 64-bit value.

The **timestamp domain** is `0` to `9223372036854775807` inclusive. A
value outside it is invalid wherever it appears: as a producer-supplied
timestamp (§3.8, §3.12), as a query time literal (§3.19), or as a value
in a result record.

The domain has no negative half. A collector MUST reject a negative
timestamp rather than storing a time before 1970, and a query whose time
arithmetic lands below zero — `SINCE 100000d ago`, for example — MUST
produce an error rather than clamping.

> [!NOTE]
> The upper bound is `i64::MAX` nanoseconds, which is the year 2262. The
> domain is stated as a closed range rather than "whatever fits" because
> both parties must agree on where the edge is: a producer that clamps
> and a collector that rejects would disagree about the same sample.

Wall-clock time is not monotonic. A collector MUST store the timestamp
it is given or derives without correcting it, and MUST NOT assume that
timestamps within one time series increase (§3.13). A clock step
backwards produces records that are out of order with respect to their
arrival, and every ordering rule in this chapter is defined to remain
total and deterministic when that happens.
